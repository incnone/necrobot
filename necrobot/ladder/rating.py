class Rating(object):
    def __init__(self, mu, sigma):
        self.mu = mu
        self.sigma = sigma

    @property
    def displayed_rating(self) -> str:
        adj_rating = int(self.mu - 3*self.sigma)
        return str(adj_rating) if adj_rating > 0 else "Unrated."
