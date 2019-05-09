from necrobot.match.matchinfo import MatchInfo


class MatchRaceData(object):
    """
    Data about all races within a match. Corresponds to a collection of entries in `match_races` in the database.
    """
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

    @property
    def lagger_wins(self):
        return min(self.r1_wins, self.r2_wins)

    def completed(self, match_info: MatchInfo):
        if match_info.is_best_of:
            return self.leader_wins > match_info.max_races // 2
        else:
            return self.num_finished >= match_info.max_races
