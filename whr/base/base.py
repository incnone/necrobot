"""Direct port from goshrine: 

https://github.com/goshrine/whole_history_rating/blob/master/lib/whole_history_rating/base.rb
"""

import math
from whr.base.game import Game
from whr.base.player import Player


class WholeHistoryRating(object):
    """
    Parameters
    ----------
    w: float
        The parameter determining the Weiner process (r_1 and r_2 are related by a normal distribution
        of variance |t_1 - t_2|w^2); units of Elo
    prior_stdev: float
        The prior will be set up so that the marginals at each r_i, for a given player, have mean 0 and
        this standard deviation; units of Elo
    verbose: bool
        If true, will output partial progress during iteration
    """
    def __init__(self, **config):
        self.config = {
            'w': 30.0,
            'prior_stdev': 400.0,
            'verbose': False
        }
        self.config.update(config)
        self.config['w2'] = self.config['w']**2
        self.config['prior_var'] = self.config['prior_stdev']**2
        self.players = dict()

    def __getattr__(self, item):
        return self.config[item]

    def reset_config(self, **config):
        self.config.update(config)
        if 'w2' not in config:
            self.config['w2'] = self.config['w']**2
        if 'prior_var' not in config:
            self.config['prior_var'] = self.config['prior_stdev']**2
        for player in self.players.values():
            player.reset_config(self.config)

    def print_ordered_ratings(self, outfile):
        players = [p for p in self.players.values() if p.player_days]
        players = sorted(players, key=lambda p: p.last_gamma, reverse=True)
        for player in players:
            elo_str = ''
            sigma_str = ''
            for pday in player.player_days:
                elo_str += '{0}: {1}, '.format(pday.day, int(round(pday.elo)))
                sigma_str += '{0}: {1}, '.format(pday.day, int(round(pday.elo_stdev)))
            if elo_str:
                elo_str = elo_str[:-2]
                sigma_str = sigma_str[:-2]

            outfile.write(
                '{name}: Elo: [{elos}] Sigma: [{sigmas}]\n'.format(
                    name=player.name,
                    elos=elo_str,
                    sigmas=sigma_str
                )
            )

    def log_likelihood_test(self, multiday_only=False):
        score = 0.0
        for player in self.players.values():
            if multiday_only and (len(player.player_days) == 1 or len(player.test_days) == 1):
                continue
            score += player.get_log_likelihood_test()
        return score

    # def log_likelihood(self):
    #     score = 0.0
    #     for player in self.players.values():
    #         score += player.log_likelihood
    #     return score

    def player_by_name(self, name):
        if name not in self.players:
            self.players[name] = Player(name, self.config)
        return self.players[name]

    def ratings_for_player(self, name):
        player = self.player_by_name(name)
        return [(dd.day, dd.elo, dd.elo_stdev,) for dd in player.player_days]

    def setup_game(self, black, white, winner, time_step, black_elo_adv=0):
        if black == white:
            raise RuntimeError('Invalid game (black = white)')

        white_player = self.player_by_name(white)
        black_player = self.player_by_name(black)
        return Game(
            black_player=black_player,
            white_player=white_player,
            winner=winner,
            time_step=time_step,
            black_elo_adv=black_elo_adv
        )

    def create_game(self, black, white, winner, time_step, black_elo_adv=0):
        game = self.setup_game(black, white, winner, time_step, black_elo_adv)
        return self.add_game(game)

    def add_game(self, game, test=False):
        game.white_player.add_game(game=game, test=test)
        game.black_player.add_game(game=game, test=test)
        if game.bpd is None:
            raise RuntimeError('Bad game: {0}'.format(str(game)))
        return game

    def iterate(self, count):
        for player in self.players.values():
            player.compute_prior_vars()
        for i in range(count):
            if self.verbose:
                print('Running iteration {}'.format(i))
            self.run_one_iteration()
        for player in self.players.values():
            player.update_variance()

    def run_one_iteration(self):
        for player in self.players.values():
            player.run_one_newton_iteration()

    def iterate_until(self, min_cycles=2, max_cycles=None, elo_diff=None):
        """TODO. Trying to be intelligent about stopping
        """
        min_cycles = max(2, min_cycles)
        cycle = 0
        rsq_diff = (elo_diff*math.log(10)/400.0)**2
        ll_init = None
        if self.verbose:
            print(
                'Iterating between {min} and {max} cycles, stopping if Elo delta is smaller than {diff}'
                .format(min=min_cycles, max=max_cycles, diff=elo_diff)
            )

        for player in self.players.values():
            player.compute_prior_vars()

        while True:
            cycle += 1
            self.run_one_iteration()

            if self.verbose:
                log_probability = 0.0
                rdelta_sqnorm = 0.0
                for player in self.players.values():
                    log_probability += player.log_probability
                    rdelta_sqnorm += player.last_rdelta_sqnorm

                if ll_init is None:
                    ll_init = log_probability

                ll_diff = log_probability - ll_init

                print(
                    'Iteration {num}: dlp={dll:0.2f}, eloDelta={elo_delta:0.4f}'.format(
                        num=cycle,
                        dll=ll_diff,
                        elo_delta=math.sqrt(rdelta_sqnorm)*400.0/math.log(10)
                    )
                )
            else:
                rdelta_sqnorm = 0.0
                for player in self.players.values():
                    rdelta_sqnorm += player.last_rdelta_sqnorm

            if ((rdelta_sqnorm < rsq_diff) or (max_cycles is not None and cycle > max_cycles)) \
                    and not (cycle < min_cycles):
                break

        for player in self.players.values():
            player.update_variance()
