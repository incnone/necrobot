from math import log, exp, pow, sqrt

LOG_10 = log(10)


def elo_to_r(elo: float) -> float:
    return elo*LOG_10/400.


def r_to_elo(r: float) -> float:
    return r*400./LOG_10


def elo_to_gamma(elo: float) -> float:
    return pow(10, elo/400.)


def gamma_to_elo(gamma: float) -> float:
    return log(gamma)*400./LOG_10


def r_to_gamma(r: float) -> float:
    return exp(r)


def gamma_to_r(gamma: float) -> float:
    return log(gamma)


def elo2_to_r2(elo2: float) -> float:
    return (elo_to_r(sqrt(elo2)))**2


def r2_to_elo2(r2: float) -> float:
    return (r_to_elo(sqrt(r2)))**2
