import necrobot.exception
from necrobot.util import seedgen
from necrobot.util.parse import matchparse

from necrobot.util.character import NDChar


class RaceInfo(object):
    @staticmethod
    def copy(race_info):
        the_copy = RaceInfo()

        the_copy.seed = race_info.seed if race_info.seed_fixed else seedgen.get_new_seed()
        the_copy.seed_fixed = race_info.seed_fixed
        the_copy.seeded = race_info.seeded

        the_copy.character = race_info.character

        the_copy.amplified = race_info.amplified
        the_copy.post_results = race_info.post_results

        the_copy.descriptor = race_info.descriptor

        the_copy.can_be_solo = race_info.can_be_solo
        the_copy.condor_race = race_info.condor_race
        the_copy.private_race = race_info.private_race

        return the_copy

    def __init__(self):
        self.seed = int(0)                   # the seed for the race
        self.seed_fixed = False              # is this specific seed preserved for rematches
        self.seeded = True                   # whether the race is run in seeded mode
        self.descriptor = 'All-zones'        # a short description (e.g. '4-shrines', 'leprechaun hunting', etc)
        self.amplified = True                # whether playing with the Amplified DLC
        self.can_be_solo = False             # whether the race can be run with only one person
        self.post_results = True             # whether to post the results in the race_results necrobot
        self.condor_race = False             # whether this is a condor race
        self.private_race = False            # whether this is a private race
        self.character = NDChar.Cadence      # the character for the race

    @property
    def character_str(self):
        return str(self.character)

    # a string "Seed: (int)" if the race is seeded, or the empty string otherwise
    @property
    def seed_str(self):
        if self.seeded:
            return 'Seed: {0}'.format(self.seed)
        else:
            return ''

    # a one-line string for identifying race format
    @property
    def format_str(self):
        char_str = str(self.character) + ' '
        if not self.amplified:
            char_str += '(No DLC) '

        desc_str = (self.descriptor + ' ') if not self.descriptor == 'All-zones' else ''
        seeded_str = 'Seeded' if self.seeded else 'Unseeded'
        addon_str = ''
        if addon_str:
            addon_str = ' -- {0}'.format(addon_str.rstrip())

        return char_str + desc_str + seeded_str + addon_str
    
    # an abbreviated string suitable for identifying this race
    @property
    def raceroom_name(self):
        if self.character is not None:
            main_identifier = str(self.character).lower()
        else:
            main_identifier = self.descriptor.lower()

        tags = 's' if self.seeded else 'u'

        return '{0}-{1}'.format(main_identifier, tags)

    def set_char(self, char_as_str):
        self.character = NDChar.fromstr(char_as_str)


def parse_args(args: list) -> RaceInfo:
    """Parses the given command-line args into a RaceInfo.
    
    Parameters
    ----------
    args: list[str]
        The list of command-line args. Warning: list will be empty after this method.

    Returns
    -------
    RaceInfo
        The created RaceInfo.
        
    Raises
    ------
    ParseException
    """
    return parse_args_modify(args, RaceInfo())


def parse_args_modify(args: list, race_info: RaceInfo) -> RaceInfo:
    """Returns a new RaceInfo which is the supplied RaceInfo with information changed as specified
    by args.
    
    Parameters
    ----------
    args: list[str]
        The list of command-line args. Warning: list will be empty after this method.
    race_info: RaceInfo
        The RaceInfo to get a modified version of.

    Returns
    -------
    RaceInfo
        The modified RaceInfo.
        
    Raises
    ------
    ParseException
    """
    return parse_from_dict(matchparse.parse_matchtype_args(args), race_info)


def parse_from_dict(args_dict: dict, race_info: RaceInfo) -> RaceInfo:
    """Returns a new RaceInfo which is the supplied RaceInfo with information changed as specified
    by args_dict.
    
    Parameters
    ----------
    args_dict: dict[str, list[str]]
        The parsed dict of command-line args.
    race_info: RaceInfo
        The RaceInfo to get a modified version of.

    Returns
    -------
    RaceInfo
        The modified RaceInfo.
        
    Raises
    ------
    ParseException
    """
    new_race_info = RaceInfo.copy(race_info)

    for keyword, params in args_dict.items():
        if keyword == 'seeded':
            new_race_info.seeded = True
        elif keyword == 'unseeded':
            new_race_info.seeded = False
        elif keyword == 'seed':
            try:
                new_race_info.seed = int(params[0])
            except ValueError:
                raise necrobot.exception.ParseException("Couldn't parse {0} as a seed.".format(params[0]))
        elif keyword == 'character':
            character_ = NDChar.fromstr(params[0])
            if character_ is None:
                raise necrobot.exception.ParseException("Couldn't parse {0} as a character.".format(params[0]))
            new_race_info.character = character_
        elif keyword == 'nodlc':
                new_race_info.amplified = False
        elif keyword == 'dlc':
            new_race_info.amplified = True
        elif keyword == 'nopost':
            new_race_info.post_results = False
        elif keyword == 'post':
            new_race_info.post_results = True
        elif keyword == 'custom':
            new_race_info.descriptor = params[0]

    return new_race_info
