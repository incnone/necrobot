class MatchRaceData(object):
    def __init__(self, finished=0, canceled=0, r1_wins=0, r2_wins=0):
        self.num_finished = finished
        self.num_canceled = canceled
        self.r1_wins = r1_wins
        self.r2_wins = r2_wins

    @property
    def num_races(self):
        return self.num_finished + self.num_canceled

    @property
    def leader_wins(self):
        return max(self.r1_wins, self.r2_wins)
