import trueskill
from math import erf, sqrt
from necrobot.util import console


class Rating(object):
    @staticmethod
    def make_from_trueskill(rating):
        return Rating(rating.mu, rating.sigma)

    def __init__(self, mu, sigma):
        self.mu = mu
        self.sigma = sigma

    @property
    def displayed_rating(self):
        return self.mu - 3*self.sigma

    @property
    def as_trueskill(self):
        return trueskill.global_env().create_rating(self.mu, self.sigma)


def init():
    trueskill.setup(
        mu=1600,                    # mu of the prior
        sigma=400,                  # sigma of the prior
        beta=200,                   # distance to guarantee 76% of winning (rec = sigma/2)
        tau=4,                      # dynamic ratings factor (increases sigma over time) (rec = sigma/100)
        draw_probability=0.0,       # probability of a draw
        backend=None)               # allows for mpmath/scipy normal distribution implementations


def create_rating(mu=None, sigma=None):
    return Rating.make_from_trueskill(trueskill.global_env().create_rating(mu, sigma))


def get_new_ratings(winner, loser):
    try:
        recalc_pair = trueskill.rate_1vs1(winner.as_trueskill, loser.as_trueskill)
        return Rating.make_from_trueskill(recalc_pair[0]), Rating.make_from_trueskill(recalc_pair[1])
    except FloatingPointError:
        console.error('FloatingPointError in rating.get_new_ratings.')
        return winner, loser


def get_winrate(rating_1, rating_2):
    delta_mu = rating_1.mu - rating_2.mu
    if delta_mu >= 0:
        beta = trueskill.global_env().beta
        denom = sqrt(2 * (2 * beta * beta + rating_1.sigma * rating_1.sigma + rating_2.sigma * rating_2.sigma))
        return (erf(delta_mu/denom) + 1.0)/2.0
    else:
        return 1.0 - get_winrate(rating_2, rating_1)
