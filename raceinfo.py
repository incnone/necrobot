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

import seedgen

NDChars = ['Cadence', 'Melody', 'Aria', 'Dorian', 'Eli', 'Monk', 'Dove', 'Coda', 'Bolt', 'Bard']

## The "parse" commands below attempt to parse the leftmost arguments of an argument list as commands to modify a race_info.
## If successful, they pop the relevant args from the list, add to the race_info, and return True. Otherwise, they return false.

# For any word cmd in cmd_list, returns as below if args has one of the following forms:
# args = [cmd=x, ...] ---> returns [1, x]
# args = [-cmd, x, ...] ---> returns [2, x]
# Otherwise, returns [0, ''].
def _get_parseval_for_cmd(cmd_list, args):
    if args:
        cmd = args[0]
        if cmd.startswith('-') and (cmd[1:] in cmd_list) and len(args) >= 2:
            return [2, args[1]]
        else:
           cmd_split = cmd.split('=', 1)
           if len(cmd_split) == 2 and cmd_split[0] in cmd_list:
               return [1, cmd_split[1]]
    return [0, '']
        

def _parse_seed(args, race_info):
    command_list = ['seed']
    parseval = _get_parseval_for_cmd(command_list, args)

    try:
        race_info.seed = int(parseval[1])
        pop_num = parseval[0]
        while pop_num > 0:
            pop_num -= 1
            args.pop(0)
        return True
    except ValueError:
        return False
        
def _parse_seeded(args, race_info):
    seeded_commands = ['s', '-s', 'seeded', '-seeded', 'seeded=true']
    unseeded_commands = ['u', '-u', 'unseeded', '-unseeded', 'seeded=false']

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
        if args[0].capitalize() in NDChars:
            race_info.character = args[0].capitalize()
            args.pop(0)
            return True
        else:
            parseval = _get_parseval_for_cmd(command_list, args)
            if parseval[1].capitalize() in NDChars:
                race_info.character = parseval[1].capitalize()
                pop_num = parseval[0]
                while pop_num > 0:
                    pop_num -= 1
                    args.pop(0)
                return True
            
    return False

##def _parse_sudden_death(args, race_info):
##
##def _parse_flagplant(args, race_info):

def _parse_desc(args, race_info):
    command_list = ['custom']
    
    parseval = _get_parseval_for_cmd(command_list, args)
    pop_num = parseval[0]
    if pop_num:
        race_info.descriptor = parseval[1]
        while pop_num > 0:
            pop_num -= 1
            args.pop(0)
        return True
    return False
    

# Attempts to parse the given command-line args into a race-info
# Returns True on success, False on failure
# Warning: destroys information in the list args
def parse_args(args):
    race_info = RaceInfo()

    set_seed = False    #keep track of whether we've found args for each field
    set_seeded = False  
    set_char = False
    set_desc = False
    set_sd = False
    set_fp = False

    while args:
        if _parse_seed(args, race_info):
            if set_seed:
                return None
            else:
                set_seed = True
        elif _parse_seeded(args, race_info):
            if set_seeded:
                return None
            else:
                set_seeded = True
        elif _parse_char(args, race_info):
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
        elif _parse_desc(args, race_info):
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

    return race_info

class RaceInfo(object):
    seed = int(0)                   #the seed for the race
    seed_fixed = False              #True means the specific seed is part of the race rules (seed doesn't change on rematch)
    seeded = True                   #whether the race is run in seeded mode
    character = 'Cadence'           #the character for the race
    descriptor = 'All-zones'        #a short description (e.g. '4-shrines', 'leprechaun hunting', etc)
    sudden_death = False            #whether the race is sudden-death (cannot restart race after death)
    flagplant = False               #whether flagplanting is considered as a victory condition

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
    
    #returns a (possibly multi-line) string that can be used to header results for the race
    def info_str(self):             
        seeded_rider = '\n'
        if self.seeded:
            seeded_rider += 'Seed: {0}\n'.format(self.seed)
        
        return self.format_str() + seeded_rider

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
