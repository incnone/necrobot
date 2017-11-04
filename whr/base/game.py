"""Direct port from goshrine: 

https://github.com/goshrine/whole_history_rating/blob/master/lib/whole_history_rating/game.rb
"""

import math
from whr.base.exception import UnstableRatingException
from whr.base.player import Player


class Game(object):
    def __init__(self, black_player, white_player, winner, time_step, black_elo_adv=0.0):
        self.day = time_step
        self.black_player = black_player    # type: Player
        self.white_player = white_player    # type: Player
        self.winner = winner
        self.bpd = None
        self.wpd = None
        self.black_elo_adv = black_elo_adv

    def __str__(self):
        format_str = 'W:{w_name}(r={wr}) B:{b_name}(r={br}) Winner: {winner} Day: {day}'
        return format_str.format(
            w_name=self.white_player.name,
            b_name=self.black_player.name,
            wr=self.wpd.r if self.wpd is not None else '?',
            br=self.bpd.r if self.bpd is not None else '?',
            winner=self.winner,
            day=self.day
        )

    @property
    def winner_player(self):
        if self.winner == 'W':
            return self.white_player
        elif self.winner == 'B':
            return self.black_player
        else:
            raise RuntimeError('Winner not set to W or B.')

    @property
    def white_win_probability(self):
        return self.wpd.gamma/(self.wpd.gamma + self.opponents_gamma(self.white_player))

    @property
    def black_win_probability(self):
        return self.bpd.gamma/(self.bpd.gamma + self.opponents_gamma(self.black_player))

    def opponents_gamma(self, player):
        handicap_factor = 1.0
        if self.black_elo_adv:
            handicap_factor = math.pow(10, self.black_elo_adv/400)

        if player == self.white_player:
            opp_gamma = self.bpd.gamma*handicap_factor
        elif player == self.black_player:
            opp_gamma = self.wpd.gamma/handicap_factor
        else:
            raise RuntimeError('{0} is not in the game.'.format(str(player)))

        if opp_gamma == 0.0 or not math.isfinite(opp_gamma):
            raise UnstableRatingException('Bad adjusted gamma: {}'.format(str(self)))
        return opp_gamma

    def opponent(self, player):
        if player == self.white_player:
            return self.black_player
        elif player == self.black_player:
            return self.white_player
        else:
            raise RuntimeError('{0} is not in the game.'.format(str(player)))
