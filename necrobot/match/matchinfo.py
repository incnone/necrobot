from necrobot.util.parse import matchparse
from necrobot.race import raceinfo

from necrobot.race.raceinfo import RaceInfo
from necrobot.util.parse.exception import ParseException


class MatchInfo(object):
    @staticmethod
    def copy(match_info):
        the_copy = MatchInfo()
        the_copy.max_races = match_info.max_races
        the_copy.is_best_of = match_info.is_best_of
        the_copy.ranked = match_info.ranked
        the_copy.race_info = RaceInfo.copy(match_info.race_info)
        return the_copy

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


def parse_args(args: list) -> MatchInfo:
    """Parses the given command-line args into a RaceInfo.
    
    Parameters
    ----------
    args: list[str]
        The list of command-line args. Warning: list will be empty after this method.

    Returns
    -------
    MatchInfo
        The created MatchInfo.
        
    Raises
    ------
    ParseException
    """
    return parse_args_modify(args, MatchInfo())


def parse_args_modify(args: list, match_info: MatchInfo) -> MatchInfo:
    """Returns a new MatchInfo which is the supplied MatchInfo with information changed as specified
    by args.
    
    Parameters
    ----------
    args: list[str]
        The list of command-line args. Warning: list will be empty after this method.
    match_info: MatchInfo
        The RaceInfo to get a modified version of.

    Returns
    -------
    MatchInfo
        The modified MatchInfo.
        
    Raises
    ------
    ParseException
    """
    new_match_info = MatchInfo.copy(match_info)
    parsed_dict = matchparse.parse_matchtype_args(args)
    new_match_info.race_info = raceinfo.parse_from_dict(parsed_dict, match_info.race_info)
    for keyword, params in parsed_dict.items():
        if keyword == 'bestof':
            try:
                new_match_info.max_races = int(params[0])
            except ValueError:
                raise ParseException("Couldn't interpret {0} as a number of races.".format(params[0]))
            new_match_info.is_best_of = True
        elif keyword == 'repeat':
            try:
                new_match_info.max_races = int(params[0])
            except ValueError:
                raise ParseException("Couldn't interpret {0} as a number of races.".format(params[0]))
            new_match_info.is_best_of = False
        elif keyword == 'ranked':
            new_match_info.ranked = True
        elif keyword == 'unranked':
            new_match_info.ranked = False

    return new_match_info
