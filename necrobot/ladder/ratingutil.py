from math import sqrt, erf, log2
from typing import Tuple

import trueskill

from necrobot.util import console
from necrobot.ladder.rating import Rating


def init():
    trueskill.setup(
        mu=1600,                    # mu of the prior
        sigma=400,                  # sigma of the prior
        beta=200,                   # distance to guarantee 76% of winning (rec = sigma/2)
        tau=4,                      # dynamic ratings factor (increases sigma over time) (rec = sigma/100)
        draw_probability=0.0,       # probability of a draw
        backend=None)               # allows for mpmath/scipy normal distribution implementations


def create_rating(mu=None, sigma=None) -> Rating:
    return Rating.make_from_trueskill(trueskill.global_env().create_rating(mu, sigma))


def get_new_ratings(rating_1: Rating, rating_2: Rating, winner=1) -> Tuple[Rating, Rating]:
    try:
        if winner == 1:
            recalc_pair = trueskill.rate_1vs1(rating_1.as_trueskill, rating_2.as_trueskill)
            return Rating.make_from_trueskill(recalc_pair[0]), Rating.make_from_trueskill(recalc_pair[1])
        elif winner == 2:
            recalc_pair = trueskill.rate_1vs1(rating_2.as_trueskill, rating_1.as_trueskill)
            return Rating.make_from_trueskill(recalc_pair[1]), Rating.make_from_trueskill(recalc_pair[0])
        else:
            return rating_1, rating_2

    except FloatingPointError:
        console.warning('FloatingPointError in rating.get_new_ratings.')
        return rating_1, rating_2


def get_winrate(rating_1: Rating, rating_2: Rating) -> float:
    delta_mu = rating_1.mu - rating_2.mu
    if delta_mu >= 0:
        beta = trueskill.global_env().beta
        denom = sqrt(2 * (2 * beta * beta + rating_1.sigma * rating_1.sigma + rating_2.sigma * rating_2.sigma))
        return (erf(delta_mu/denom) + 1.0)/2.0
    else:
        return 1.0 - get_winrate(rating_2, rating_1)


def get_entropy(rating_1: Rating, rating_2: Rating) -> float:
    p1 = get_winrate(rating_1, rating_2)
    p2 = 1.0 - p1
    try:
        return -(p1*log2(p1) + p2*log2(p2))
    except ValueError:  # If p1 or p2 is too close to zero, there's no expected information
        return 0.0
