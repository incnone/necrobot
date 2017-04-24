from necrobot.race.raceinfo import RaceInfo


class MatchInfo(object):
    def __init__(
            self,
            max_races: int = None,
            is_best_of: bool = None,
            ranked: bool = None,
            race_info: RaceInfo = None
    ):
        self.max_races = max_races if max_races is not None else 3
        self.is_best_of = is_best_of if is_best_of is not None else False
        self.ranked = ranked if ranked is not None else False
        self.race_info = race_info if race_info is not None else RaceInfo()

    @property
    def format_str(self) -> str:
        """Get a string describing the match format."""
        if self.is_best_of:
            match_format_info = 'best-of-{0}'.format(self.max_races)
        else:
            match_format_info = '{0} races'.format(self.max_races)

        ranked_str = 'ranked' if self.ranked else 'unranked'

        return '{0}, {1}, {2}'.format(self.race_info.format_str, match_format_info, ranked_str)
