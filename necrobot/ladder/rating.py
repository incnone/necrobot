import trueskill


class Rating(object):
    @staticmethod
    def make_from_trueskill(rating):
        return Rating(rating.mu, rating.sigma)

    def __init__(self, mu, sigma):
        self.mu = mu
        self.sigma = sigma

    @property
    def displayed_rating(self):
        return int(self.mu - 3*self.sigma)

    @property
    def as_trueskill(self):
        return trueskill.global_env().create_rating(self.mu, self.sigma)
