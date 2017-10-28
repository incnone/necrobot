"""Port from goshrine: 

https://github.com/goshrine/whole_history_rating/blob/master/lib/whole_history_rating/player.rb
"""

import itertools
import math
from math import sqrt, log
import numpy
import numpy.linalg
import unittest
from typing import List, Optional, Tuple

import conversions
from playerday import PlayerDay


class Player(object):
    def __init__(self, name: str, config: dict):
        """
        Data
        ----
        name: str
            The player's name
        prior_var: float
            The variance to be used on the prior at day=0. (Mean is 0.)
        w2: float
            The parameter for the Weiner process for rating spread between times, which has variance |t1 - t2|*w2
        player_days: List[PlayerDay]
            A list of all games, indexed by day
        """
        self.name = name                                                # type: str
        self.prior_var = conversions.elo2_to_r2(config['prior_var'])    # type: float
        self.w2 = conversions.elo2_to_r2(config['w2'])                  # type: float
        self.player_days = list()                                       # type: List[PlayerDay]
        self.test_days = list()                                         # type: List[PlayerDay]

        self._prior_precisions = None                                   # type: numpy.ndarray
        self._cached_weiner_sigma2s = None                              # type: numpy.ndarray
        self._cached_lp = None                                          # type: float
        self._cached_lp_gradient = None                                 # type: numpy.ndarray
        self._cached_lp_hessian = None                                  # type: numpy.matrix
        self._cached_lp_covariance = None                               # type: numpy.matrix

    def __eq__(self, other):
        return self.name == other.name

    def __str__(self):
        return self.name

    @property
    def numdays(self) -> int:
        return len(self.player_days)

    @property
    def weiner_sigma2s(self) -> numpy.ndarray:
        return self._cached_weiner_sigma2s

    @property
    def rlist(self) -> List[float]:
        return [day.r for day in self.player_days]

    @property
    def last_gamma(self) -> Optional[float]:
        if self.player_days:
            return self.player_days[-1].gamma
        else:
            return None

    @property
    def log_probability(self) -> float:
        """Return the log-probability of the stored sequence of PlayerDays"""
        if self._cached_lp is None:
            n = len(self.player_days)
            if n == 0:
                return 0.0

            sigma2 = self.weiner_sigma2s

            r = list([dd.r for dd in self.player_days])
            ll_tally = 0

            for i in range(0, n):
                # ll_prior = -0.5*math.log(2*math.pi/self._prior_precisions[i]) - self._prior_precisions[i]*(r[i]**2)/2
                ll_prior = -self._prior_precisions[i]*(r[i]**2)/2
                ll_day = self.player_days[i].log_likelihood
                ll_tally += ll_prior + ll_day

            for i in range(1, n):
                ll_weiner = -(0.5*log(2*math.pi*sigma2[i]) + (r[i] - r[i-1])**2/(2*sigma2[i]))
                ll_tally += ll_weiner

            self._cached_lp = ll_tally

        # noinspection PyTypeChecker
        return self._cached_lp

    @property
    def lp_hessian(self) -> numpy.matrix:
        """Get the Hessian of the log-probability function (with respect to the r[t_i] variables, for the 
        times in self.player_days)"""
        if self._cached_lp_hessian is None:
            n = self.numdays
            sigma2 = self.weiner_sigma2s
            hess = numpy.matrix(numpy.zeros(shape=(n, n,)))

            # Diagonal entries
            for diag in range(n):
                prior = -self._prior_precisions[diag]
                if diag < n - 1:
                    prior -= 1.0 / sigma2[diag+1]
                if diag > 0:
                    prior -= 1.0 / sigma2[diag]

                hess[diag, diag] = self.player_days[diag].log_likelihood_second_derivative + prior

            # Superdiagonal
            for row in range(n-1):
                col = row + 1
                hess[row, col] = 1.0 / sigma2[col]

            # Subdiagonal
            for row in range(1, n):
                col = row - 1
                hess[row, col] = 1.0 / sigma2[row]

            self._cached_lp_hessian = hess

        # noinspection PyTypeChecker
        return self._cached_lp_hessian

    @property
    def lp_gradient(self) -> numpy.ndarray:
        """Get the gradient of the log-probability function (with respect to the r[t_i] variables, for the 
        times in self.player_days)"""
        if self._cached_lp_gradient is None:
            n = self.numdays
            r = self.rlist
            grad = numpy.zeros(shape=(n,))
            sigma2 = self.weiner_sigma2s
            for j, day in enumerate(self.player_days):
                prior = -r[j]*self._prior_precisions[j]
                if j < n-1:
                    prior += -(r[j] - r[j+1])/sigma2[j+1]

                if j > 0:
                    prior += -(r[j] - r[j-1])/sigma2[j]

                grad[j] = day.log_likelihood_derivative + prior

            self._cached_lp_gradient = grad

        # noinspection PyTypeChecker
        return self._cached_lp_gradient

    @property
    def lp_covariance(self) -> numpy.matrix:
        """Gets an approximate partial covariance matrix by partially inverting the Hessian.

        Important: Only the diagonal, superdiagonal, and subdiagonal of the result are filled.

        See Appendix B.2 of Remi's paper.
        """
        if self._cached_lp_covariance is None:
            hess = self.lp_hessian

            n = hess.shape[0]
            cov = numpy.matrix(numpy.zeros(shape=(n, n,)))

            if n == 1:
                cov[0, 0] = -1 / hess[0, 0]
                return cov

            a, d, b = self._get_adb_for_lu(hess=hess)
            ap, dp, bp = self._get_adb_for_ul(hess=hess)

            v = numpy.zeros(shape=(n,))
            for i in range(0, n - 1):
                v[i] = dp[i + 1] / (b[i] * bp[i + 1] - d[i] * dp[i + 1])
            v[n - 1] = -1 / d[n - 1]

            for row in range(n):
                cov[row, row] = v[row]
            for row in range(n - 1):
                col = row + 1
                cov[row, col] = -(a[col] * v[col])
            for row in range(1, n):
                col = row - 1
                cov[row, col] = -(a[row] * v[row])

            self._cached_lp_covariance = cov

        # noinspection PyTypeChecker
        return self._cached_lp_covariance

    @property
    def last_rdelta_sqnorm(self) -> float:
        """Gets the squared norm of the change in r since the last iteration."""
        sqnorm = 0.0
        for day in self.player_days:
            sqnorm += day.last_rdelta**2
        return sqnorm

    def r_at_time(self, time_step: int) -> float:
        """Get the interpolated r value for the given time step.
        
        See Appendix C of Remi's paper.
        """
        last_r = None
        last_day = None
        for day in self.player_days:
            if day.day == time_step:
                return day.r
            elif day.day > time_step:
                if last_r is None:
                    return day.r
                return (day.r*(day.day - time_step) + last_r*(time_step - last_day)) / (day.day - last_day)
            else:
                last_r = day.r
                last_day = day.day
        return last_r

    def var_at_time(self, time_step: int) -> float:
        """Get the interpolated variance for the given time step.
        
        See Appendix C of Remi's paper.
        """
        last_timestep = None
        for idx, day in enumerate(self.player_days):
            if day.day == time_step:
                return day.variance
            elif day.day > time_step:
                if idx == 0:
                    return day.variance
                t2 = last_timestep
                t1 = day.day
                t = time_step
                cov = self.lp_covariance
                s11 = cov[idx-1, idx-1]
                s12 = cov[idx-1, idx]
                s22 = cov[idx, idx]
                return (t2-t)*(t-t1)/(t2-t1) + (((t2-t)**2)*s11 + 2*(t2-t)*(t-t1)*s12 + ((t-t1)**2)*s22) / ((t2-t1)**2)
            else:
                last_timestep = day.day

    def get_log_likelihood_test(self) -> float:
        # Set ratings on test days
        for day in self.test_days:
            r = self.r_at_time(day.day)
            day.r = r if r is not None else 0.0

        # Compute log-likelihood
        ll_tally = 0
        for day in self.test_days:
            ll_tally += day.log_likelihood
        return ll_tally

    def invalidate_cache(self) -> None:
        for day in self.player_days:
            day.invalidate_cache()

        self._cached_weiner_sigma2s = None
        self._cached_lp = None
        self._cached_lp_hessian = None
        self._cached_lp_gradient = None
        self._cached_lp_covariance = None

    def reset_config(self, config) -> None:
        self.prior_var = conversions.elo2_to_r2(config['prior_var'])
        self.w2 = conversions.elo2_to_r2(config['w2'])
        self.invalidate_cache()
        self._compute_sigma2()

    def run_one_newton_iteration(self) -> None:
        self.invalidate_cache()
        if len(self.player_days) == 1:
            self._update_by_1d_newton()
        elif len(self.player_days) > 1:
            self._update_by_ndim_newton()

    def update_variance(self) -> None:
        """Update the 'variance' property in each of our PlayerDays. Done a posteriori."""
        if self.player_days:
            cov = self.lp_covariance
            n = cov.shape[0]
            variance = [cov[i, i] for i in range(n)]
            for var, day in itertools.zip_longest(variance, self.player_days):
                day.variance = var

    def add_game(self, game, test=False) -> None:
        """Add the game to our list.
        
        Parameters
        ----------
        game: Game
            The game to add
        test: bool
            If true, will not use this game to determine ratings        
        """
        day_list = self.test_days if test else self.player_days

        if not day_list:
            new_pday = PlayerDay(player=self, day=game.day, r=0.0)
            day_list.append(new_pday)
            if not test:
                self._compute_sigma2()
        elif day_list[-1].day != game.day:
            if game.day < day_list[-1].day:
                raise RuntimeError('Trying to add a game that\'s earlier than a previously added game.')
            new_pday = PlayerDay(player=self, day=game.day, r=day_list[-1].r)
            day_list.append(new_pday)
            if not test:
                self._compute_sigma2()

        if game.white_player == self:
            game.wpd = day_list[-1]
        else:
            game.bpd = day_list[-1]

        day_list[-1].add_game(game)

    def compute_prior_vars(self) -> None:
        """Attempt to compute prior variances for each time step so that the marginals are all equal to the prior_var
        value in the config"""
        n = self.numdays
        if n == 0:
            return
        if n == 1:
            self._prior_precisions = numpy.full(shape=(n,), fill_value=1.0/self.prior_var)
            return

        s = 1.0/self.prior_var
        a = self.weiner_sigma2s
        p = numpy.empty(shape=(n,))
        y = numpy.empty(shape=(n,))

        def q(ai: float) -> float:
            result_n = (ai*s - 2 - sqrt(4 + (ai*s)**2))/(2*ai)
            return result_n if result_n > 0 else (ai*s - 2 + sqrt(4 + (ai*s)**2))/(2*ai)

        p[0] = q(a[1])
        y[0] = p[0]/(1.0 + a[1]*p[0])
        for i in range(1, n-1):
            p[i] = q(a[i+1]) - y[i-1]
            y[i] = (p[i] + y[i-1])/(1 + a[i+1]*(p[i] + y[i-1]))
        p[n-1] = s - y[n-2]

        self._prior_precisions = p

    def _get_marginals(self, priors: numpy.ndarray) -> numpy.ndarray:
        """Compute the marginal functions from the given priors
        P_0         P_1                         P_{n-1}
         |           |                           |
        V_0 - W_0 - V_1 - W_1 - ... - W_{n-2} - V_{n-1}
        """
        n = self.numdays
        weights = numpy.zeros(shape=(n-1,))
        for i in range(n-1):
            weights[i] = (self.player_days[i+1].day - self.player_days[i].day)*self.w2

        def transform_w(idx: int, msg: float) -> float:
            return msg / (1. + weights[idx]*msg)

        fwd_messages = numpy.zeros(shape=(n-1,))    # Msg from W_i to V_{i+1}
        bkwd_messages = numpy.zeros(shape=(n-1,))   # Msg from W_i to V_i

        # Compute message from W_i to V_{i+1}
        for i in range(n-1):
            prev_message = fwd_messages[i-1] if i > 0 else 0
            new_message = priors[i]
            fwd_messages[i] = transform_w(i, prev_message + new_message)

        # Compute message from W_i to V_i
        for i in range(n-2, -1, -1):
            prev_message = bkwd_messages[i+1] if i < n-2 else 0
            new_message = priors[i+1]
            bkwd_messages[i] = transform_w(i, prev_message + new_message)

        marginals = numpy.zeros(shape=(n,))
        for i in range(n):
            marginals[i] = priors[i]
            if i > 0:
                marginals[i] += fwd_messages[i-1]
            if i < n-1:
                marginals[i] += bkwd_messages[i]
            marginals[i] = marginals[i]

        return marginals

    def _compute_sigma2(self) -> numpy.ndarray:
        """Get the list of conditional variances by day, due to the Weiner process alone
        
        Returns
        -------
        numpy.ndarray
            The ith component of the return is the variance between times i and (i-1)
        """
        n = self.numdays
        self._cached_weiner_sigma2s = numpy.zeros(shape=(n,))
        if n == 0:
            return self._cached_weiner_sigma2s

        self._cached_weiner_sigma2s[0] = None
        for i in range(1, n):
            self._cached_weiner_sigma2s[i] = abs(self.player_days[i].day - self.player_days[i - 1].day) * self.w2
        return self._cached_weiner_sigma2s

    def _update_by_1d_newton(self) -> None:
        day = self.player_days[0]
        ll_2nd_der = -self._prior_precisions[0] + day.log_likelihood_second_derivative
        ll_1st_der = -day.r*self._prior_precisions[0] + day.log_likelihood_derivative
        day.last_rdelta = ll_1st_der/ll_2nd_der
        day.r -= day.last_rdelta

    def _update_by_ndim_newton(self) -> None:
        hess = self.lp_hessian
        grad = self.lp_gradient

        n = hess.shape[0]
        a, d, b = self._get_adb_for_lu(hess=hess)

        # Find y so that Ly = grad
        y = numpy.zeros(shape=(n,))
        y[0] = grad[0]
        for i in range(1, n):
            y[i] = grad[i] - a[i]*y[i-1]

        # Find x so that Ux = y (and hence Hx = grad)
        x = numpy.zeros(shape=(n,))
        x[n-1] = y[n-1]/d[n-1]
        for i in range(n-2, -1, -1):
            x[i] = (y[i] - b[i]*x[i+1])/d[i]

        # # Check for unstable ratings TODO: I don't understand this
        # for adj_r in [z[0] - z[1] for z in itertools.zip_longest(r, x)]:
        #     if adj_r > 650:
        #         raise UnstableRatingException('Unstable r {0} on player {1}'.format(adj_r, str(self)))

        # Update the ratings
        for i, day in enumerate(self.player_days):
            # print('{0} x[{2}] = {1}'.format(self.name, x[i], i))
            day.r -= x[i]
            day.last_rdelta = x[i]

    @staticmethod
    def _get_adb_for_lu(hess) -> Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]:
        """Constants for LU decomposition of Hessian.
        
        a's are the lower diagonal of L, d's the diagonal of U, b's upper diagonal of U
        
        See also Appendix B of Remi's paper.
        """
        n = hess.shape[0]

        a = numpy.zeros(shape=(n,))
        d = numpy.zeros(shape=(n,))
        b = numpy.zeros(shape=(n,))

        d[0] = hess[0, 0]
        for i in range(1, n):
            b[i-1] = hess[i-1, i]
            a[i] = hess[i, i-1] / d[i-1]
            d[i] = hess[i, i] - a[i]*b[i-1]

        return a, d, b

    @staticmethod
    def _get_adb_for_ul(hess) -> Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]:
        """Constants for UL decomposition of Hessian.
        
        a's are the upper diagonal of U, d's the diagonal of L, b's lower diagonal of L
        
        See also Appendix B of Remi's paper.
        """
        n = hess.shape[0]

        a = numpy.zeros(shape=(n,))
        d = numpy.zeros(shape=(n,))
        b = numpy.zeros(shape=(n,))

        d[n-1] = hess[n-1, n-1]
        if n > 1:
            b[n-1] = hess[n-1, n-2]
            for i in range(n-2, -1, -1):
                a[i] = hess[i, i+1] / d[i+1]
                d[i] = hess[i, i] - a[i]*b[i+1]
                if i >= 1:
                    b[i] = hess[i, i-1]

        return a, d, b


class TestComputePriors(unittest.TestCase):
    player = None
    num_games = 8

    @classmethod
    def setUpClass(cls):
        config = {
            'w2': 100.0,
            'prior_var': 400.0
        }
        cls.player = Player(name='test_player', config=config)
        for i in range(1, cls.num_games + 1):
            player_day = PlayerDay(player=cls.player, day=i, r=0.0)
            cls.player.player_days.append(player_day)
        cls.player._compute_sigma2()

    def test_get_marginals(self):
        n = self.player.numdays
        prior_vars = numpy.full(shape=(n,), fill_value=self.player.prior_var)
        prior_vars[n-1] += 0.01
        marginals = self.player._get_marginals(priors=prior_vars)
        expected = [0.00518212, 0.00395495, 0.00351044, 0.00337629, 0.00340998, 0.00364729, 0.00434036, 0.00622559]
        for marginal, expect in zip(marginals, expected):
            self.assertAlmostEqual(marginal, expect)

    def test_compute_priors(self):
        self.player.compute_prior_vars()
        marginals = list(self.player._get_marginals(priors=self.player._prior_precisions))
        for marginal in marginals:
            self.assertAlmostEqual(marginal, 1./self.player.prior_var)
