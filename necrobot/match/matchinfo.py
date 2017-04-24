from necrobot.race.raceinfo import RaceInfo


class MatchInfo(object):
    def __init__(
            self,
            max_races: int = 3,
            is_best_of: bool = False,
            ranked: bool = False,
            race_info: RaceInfo = RaceInfo()
    ):
        self.max_races = max_races
        self.is_best_of = is_best_of
        self.ranked = ranked
        self.race_info = race_info
