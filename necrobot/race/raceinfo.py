# Class holding info data for a race.
# Examples of info_str output:

# Cadence Seeded
# Seed: 1234567

# Coda Unseeded -- Flagplant

# Bolt Seeded -- Sudden Death Flagplant
# Seed: 1234567

# Cadence 4-Shrine Unseeded -- Flagplant

# Examples of raceroom_str output:

# cadence-s
# coda-uf
# bolt-sdf
# 4-shrine-uf

from ..command import clparse
from ..util import character, seedgen

SEEDED_FLAG = int(pow(2, 0))
SUDDEN_DEATH_FLAG = int(pow(2, 1))
FLAGPLANT_FLAG = int(pow(2, 2))
AMPLIFIED_FLAG = int(pow(2, 3))


def _parse_amplified(args, race_info):
    command_list = ['nodlc']
    if args and args[0] in command_list:
        race_info.amplified = False
        args.pop(0)
        return True
    return False


def _parse_seed(args, race_info):
    # note: this allows `-s (int)` to set a specific seed, while `-s` just sets seeded.
    # important that _parse_seed be called before _parse_seeded for this to work.
    command_list = ['seed', 's'] 
    if args and len(args) >= 2 and args[0] in command_list:
        try:
            race_info.seed = int(args[1])
            args.pop(0)
            args.pop(0)
            return True
        except ValueError:
            return False
    return False


def _parse_seeded(args, race_info):
    seeded_commands = ['s', 'seeded']
    unseeded_commands = ['u', 'unseeded']

    if args:
        if args[0] in seeded_commands:
            race_info.seeded = True
            args.pop(0)
            return True
        elif args[0] in unseeded_commands:
            race_info.seeded = False
            args.pop(0)
            return True
    return False        


def _parse_char(args, race_info):
    command_list = ['c', 'char', 'character']

    if args:
        if len(args) >= 2 and args[0] in command_list:
            char = character.get_char_from_str(args[1])
            if char is not None:
                race_info.set_char(args[1].capitalize())
                args.pop(0)
                args.pop(0)
                return True
        else:
            char = character.get_char_from_str(args[0])
            if char is not None:
                race_info.set_char(args[0].capitalize())
                args.pop(0)
                return True
            
    return False


def _parse_desc(args, race_info):
    command_list = ['custom']

    if args and len(args) >= 2 and args[0] in command_list:
        args.pop(0)
        desc = ''
        for arg in args:
            desc += arg + ' '
        race_info.descriptor = desc[:-1]
        return True
    return False
    

# Attempts to parse the given command-line args into a race-info
# Returns True on success, False on failure
# Warning: destroys information in the list args
def parse_args(args):
    race_info = RaceInfo()
    return parse_args_modify(args, race_info)


def parse_args_modify(args, race_info):
    set_seed = False    # keep track of whether we've found args for each field
    set_seeded = False  
    set_char = False
    set_desc = False
    # set_sd = False
    # set_fp = False

    while args:
        next_cmd_args = clparse.pop_command(args)
        if not next_cmd_args:
            next_cmd_args.append(args[0])
            args.pop(0)
            
        if _parse_seed(next_cmd_args, race_info):
            if set_seed:
                return None
            else:
                set_seed = True
        elif _parse_seeded(next_cmd_args, race_info):
            if set_seeded:
                return None
            else:
                set_seeded = True
        elif _parse_char(next_cmd_args, race_info):
            if set_char:
                return None
            else:
                set_char = True
        # elif parse_sudden_death(args, race_info):
        #     if set_sd:
        #         return False
        #     else:
        #         set_seeded = True
        # elif parse_flagplant(args, race_info):
        #     if set_fp:
        #         return False
        #     else:
        #         set_seeded = True
        elif _parse_desc(next_cmd_args, race_info):
            if set_desc:
                return None
            else:
                set_desc = True
        else:
            return None

    if race_info.seeded:
        race_info.seed_fixed = set_seed
        if not set_seed:
            race_info.seed = seedgen.get_new_seed()
    elif set_seed and set_seeded:   # user set a seed and asked for unseeded, so throw up our hands
        return None
    elif set_seed:
        race_info.seeded = True

    return race_info    


class RaceInfo(object):
    @staticmethod
    def copy(race_info):
        the_copy = RaceInfo()
        the_copy.seed = race_info.seed if race_info.seed_fixed else seedgen.get_new_seed()
        the_copy.seed_fixed = race_info.seed_fixed
        the_copy.seeded = race_info.seeded
        the_copy.descriptor = race_info.descriptor
        the_copy.sudden_death = race_info.sudden_death
        the_copy.flagplant = race_info.flagplant
        the_copy.amplified = race_info.amplified
        the_copy._character = race_info.character
        return the_copy

    def __init__(self):
        self.seed = int(0)                   # the seed for the race
        self.seed_fixed = False              # is this specific seed preserved for rematches
        self.seeded = True                   # whether the race is run in seeded mode
        self.descriptor = 'All-zones'        # a short description (e.g. '4-shrines', 'leprechaun hunting', etc)
        self.sudden_death = False            # whether the race is sudden-death (cannot restart race after death)
        self.flagplant = False               # whether flagplanting is considered as a victory condition
        self.amplified = True                # whether playing with the Amplified DLC
        self._character = character.NDChar.Cadence  # the character for the race

    @property
    def character(self):
        return self._character

    @property
    def flags(self):
        return int(self.seeded)*SEEDED_FLAG \
               + int(self.sudden_death)*SUDDEN_DEATH_FLAG \
               + int(self.flagplant)*FLAGPLANT_FLAG \
               + int(self.amplified)*AMPLIFIED_FLAG

    @property
    def character_str(self):
        return character.get_str_from_char(self._character)

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
        char_str = character.get_str_from_char(self.character) + ' '
        if not self.amplified:
            char_str += '(No DLC) '

        desc_str = (self.descriptor + ' ') if not self.descriptor == 'All-zones' else ''
        seeded_str = 'Seeded' if self.seeded else 'Unseeded'
        addon_str = ''
        if self.sudden_death:
            addon_str += "Sudden Death "
        if self.flagplant:
            addon_str += "Flagplant "
        if addon_str:
            addon_str = ' -- {0}'.format(addon_str.rstrip())

        return char_str + desc_str + seeded_str + addon_str
    
    # an abbreviated string suitable for identifying this race
    @property
    def raceroom_name(self):
        if self.character is not None:
            main_identifier = character.get_str_from_char(self.character).lower()
        else:
            main_identifier = self.descriptor.lower()

        tags = 's' if self.seeded else 'u'
        if self.sudden_death:
            tags += 'd'
        if self.flagplant:
            tags += 'f'

        return '{0}-{1}'.format(main_identifier, tags)

    def set_char(self, char_as_str):
        self._character = character.get_char_from_str(char_as_str)
