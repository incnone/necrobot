## Class holding info data for a race.
## Examples of info_str output:

## Cadence Seeded
## Seed: 1234567

## Coda Unseeded -- Flagplant

## Bolt Seeded -- Sudden Death Flagplant
## Seed: 1234567

## Cadence 4-Shrine Unseeded -- Flagplant

## Examples of raceroom_str output:

## cadence-s
## coda-uf
## bolt-sdf
## 4-shrine-uf

import clparse
import seedgen

NDChars = ['Cadence', 'Melody', 'Aria', 'Dorian', 'Eli', 'Monk', 'Dove', 'Coda', 'Bolt', 'Bard']       
SEEDED_FLAG = int(pow(2,0))
SUDDEN_DEATH_FLAG = int(pow(2,1))
FLAGPLANT_FLAG = int(pow(2,2))

def _parse_seed(args, race_info):
    #note: this allows `-s (int)` to set a specific seed, while `-s` just sets seeded.
    #important that _parse_seed be called before _parse_seeded for this to work.
    command_list = ['seed', 's'] 
    if args and len(args) >= 2 and args[0] in command_list:
        try:
            race_info.seed = int(args[1])
            args = args[2:]
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
            if args[1].capitalize() in NDChars:
                race_info.character = args[1].capitalize()
                args = args[2:]
                return True
        elif args[0].capitalize() in NDChars:
            race_info.character = args[0].capitalize()
            args = args[1:]
            return True            
            
    return False

##def _parse_sudden_death(args, race_info):
##
##def _parse_flagplant(args, race_info):

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
    set_seed = False    #keep track of whether we've found args for each field
    set_seeded = False  
    set_char = False
    set_desc = False
    set_sd = False
    set_fp = False

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
##        elif parse_sudden_death(args, race_info):
##            if set_sd:
##                return False
##            else:
##                set_seeded = True
##        elif parse_flagplant(args, race_info):
##            if set_fp:
##                return False
##            else:
##                set_seeded = True
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
    elif set_seed and set_seeded: #user set a seed and asked for unseeded, so throw up our hands
        return None
    elif set_seed:
        race_info.seeded = True

    return race_info    

class RaceInfo(object):

    def __init__(self):
        self.seed = int(0)                   #the seed for the race
        self.seed_fixed = False              #True means the specific seed is part of the race rules (seed doesn't change on rematch)
        self.seeded = True                   #whether the race is run in seeded mode
        self.character = 'Cadence'           #the character for the race
        self.descriptor = 'All-zones'        #a short description (e.g. '4-shrines', 'leprechaun hunting', etc)
        self.sudden_death = False            #whether the race is sudden-death (cannot restart race after death)
        self.flagplant = False               #whether flagplanting is considered as a victory condition

    def copy(self):
        the_copy = RaceInfo()
        the_copy.seed = self.seed if self.seed_fixed else seedgen.get_new_seed()
        the_copy.seed_fixed = self.seed_fixed
        the_copy.seeded = self.seeded
        the_copy.character = self.character
        the_copy.descriptor = self.descriptor
        the_copy.sudden_death = self.sudden_death
        the_copy.flagplant = self.flagplant
        return the_copy

    @property
    def flags(self):
        return int(self.seeded)*SEEDED_FLAG + int(self.sudden_death)*SUDDEN_DEATH_FLAG + int(self.flagplant)*FLAGPLANT_FLAG
    
    #returns a (possibly multi-line) string that can be used to header results for the race
    #depricated. do not use. use format_str and seed_str instead.
    def info_str(self):             
        seeded_rider = '\n'
        if self.seeded:
            seeded_rider += 'Seed: {0}\n'.format(self.seed)
        
        return self.format_str() + seeded_rider

    #returns a string "Seed: (int)" if the race is seeded, or the empty string otherwise
    def seed_str(self):
        if self.seeded:
            return 'Seed: {0}'.format(self.seed)
        else:
            return ''

    #returns a one-line string for identifying race format
    def format_str(self):
        char_str = (self.character.title() + ' ') if (self.character.title() in NDChars) else ''
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
    
    #returns an abbreviated string suitable for identifying this race
    def raceroom_name(self):
        main_identifier = ''
        if self.character.title() in NDChars:
            main_identifier = self.character.lower()
        else:
            main_identifier = self.descriptor.lower()

        tags = 's' if self.seeded else 'u'
        if self.sudden_death:
            tags += 'd'
        if self.flagplant:
            tags += 'f'

        return '{0}-{1}'.format(main_identifier, tags)
