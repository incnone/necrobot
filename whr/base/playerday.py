"""Direct port from goshrine: 

https://github.com/goshrine/whole_history_rating/blob/master/lib/whole_history_rating/playerday.rb
"""
import math
import conversions


class PlayerDay(object):
    def __init__(self, player, day, r):
        self.day = day
        self.player = player
        self.won_games = list()
        self.lost_games = list()
        self.r = r
        self.last_rdelta = 0.0
        self.variance = None

        # Cached data
        self._won_game_terms = None     # type: list
        self._lost_game_terms = None    # type: list

    def __str__(self):
        return '{pl} {dy} Won: {wgl} Lost: {lgl}'.format(
            pl=self.player.name,
            dy=self.day,
            wgl=self.won_game_terms,
            lgl=self.lost_game_terms
        )

    @property
    def elo_stdev(self):
        return conversions.r_to_elo(math.sqrt(self.variance))

    @property
    def gamma(self):
        return conversions.r_to_gamma(self.r)

    @gamma.setter
    def gamma(self, gamma):
        self.r = conversions.gamma_to_r(gamma)

    @property
    def elo(self):
        return conversions.r_to_elo(self.r)

    @elo.setter
    def elo(self, elo):
        self.r = conversions.elo_to_r(elo)

    @property
    def name(self):
        return self.player.name

    @property
    def won_game_terms(self) -> list:
        if self._won_game_terms is None:
            self._won_game_terms = [self._get_game_terms(game, win=True) for game in self.won_games]
        # noinspection PyTypeChecker
        return self._won_game_terms

    @property
    def lost_game_terms(self) -> list:
        if self._lost_game_terms is None:
            self._lost_game_terms = [self._get_game_terms(game, win=False) for game in self.lost_games]
        # noinspection PyTypeChecker
        return self._lost_game_terms

    @property
    def log_likelihood_second_derivative(self):
        """See Remi's appendix A.1 for constants A,B,C,D"""
        the_sum = 0.0
        for a, b, c, d in self.won_game_terms + self.lost_game_terms:
            the_sum += (c*d) / math.pow((c*self.gamma + d), 2.0)
        return -(self.gamma*the_sum)

    @property
    def log_likelihood_derivative(self):
        the_sum = 0.0
        for a, b, c, d in self.won_game_terms + self.lost_game_terms:
            the_sum += c/(c*self.gamma + d)
        return len(self.won_game_terms) - self.gamma*the_sum

    @property
    def log_likelihood(self):
        the_sum = 0.0
        for a, b, c, d in self.won_game_terms:
            the_sum += math.log(a*self.gamma) - math.log(c*self.gamma + d)
        for a, b, c, d in self.lost_game_terms:
            the_sum += math.log(b) - math.log(c*self.gamma + d)
        return the_sum

    def invalidate_cache(self):
        self._won_game_terms = None
        self._lost_game_terms = None

    def add_game(self, game):
        if game.winner_player == self.player:
            self.won_games.append(game)
        else:
            self.lost_games.append(game)

    def update_by_1d_newtons_method(self):
        self.r -= self.log_likelihood_derivative/self.log_likelihood_second_derivative

    def _get_game_terms(self, game, win):
        other_gamma = game.opponents_gamma(self.player)
        return [1.0, 0.0, 1.0, other_gamma] if win else [0.0, other_gamma, 1.0, other_gamma]
