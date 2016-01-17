## Class holding info data for a private race.

from matchinfo import MatchInfo
import clparse
import raceinfo

ADMIN_COMMANDS = ['a']
RACER_COMMANDS = ['r']
BESTOF_COMMANDS = ['bestof']
REPEAT_COMMANDS = ['repeat']
ALL_COMMANDS = ADMIN_COMMANDS + RACER_COMMANDS + BESTOF_COMMANDS + REPEAT_COMMANDS

def _parse_admins(cmd, race_private_info):
    if cmd and cmd[0] in ADMIN_COMMANDS:
        if len(cmd) >= 2:
            args = cmd[1:]
            for arg in args:
                race_private_info.admin_names.append(arg)
            return True
    return False

def _parse_racers(cmd, race_private_info):
    if cmd and cmd[0] in RACER_COMMANDS:
        if len(cmd) >= 2:
            args = cmd[1:]
            for arg in args:
                race_private_info.racer_names.append(arg)
            return True
    return False    
                
def _parse_bestof(cmd, race_private_info):
    if cmd and cmd[0] in BESTOF_COMMANDS:
        if len(cmd) == 2:
            try:                
                race_private_info.match_info.bestof = int(args[1])
                race_private_info.match_info.match_type = MatchType.bestof
                return True
            except ValueError:
                return False
    return False

def _parse_repeat(cmd, race_private_info):
    if cmd and cmd[0] in REPEAT_COMMANDS:
        if len(cmd) == 2:
            try:                
                race_private_info.match_info.repeat = int(args[1])
                race_private_info.match_info.match_type = MatchType.repeat
                return True
            except ValueError:
                return False
    return False    

# Attempts to parse the given command-line args into a race-info
# Returns True on success, False on failure
# Warning: destroys information in the list args
def parse_args(args):    
    race_private_info = RacePrivateInfo()
    commands = clparse.pop_commands_from_list(args, ALL_COMMANDS)

    set_admins = False
    set_racers = False
    set_bestof = False
    set_repeat = False

    while commands:
        cmd = commands.pop(0)
        if _parse_admins(cmd, race_private_info):
            if set_admins:
                return None
            else:
                set_admins = True
        elif _parse_racers(cmd, race_private_info):
            if set_racers:
                return None
            else:
                set_racers = True
        elif _parse_bestof(cmd, race_private_info):
            if set_bestof or set_repeat:
                return None
            else:
                set_bestof = True
        elif _parse_repeat(cmd, race_private_info):
            if set_repeat or set_bestof:
                return None
            else:
                set_repeat = True
        else:
            return None

    race_private_info.race_info = raceinfo.parse_args(args)
    if not race_private_info.race_info:
        return None
    
    return race_private_info
                
class RacePrivateInfo():
    admin_names = []
    racer_names = []
    match_info = MatchInfo()
    race_info = None
    
    def copy(self):
        the_copy = RacePrivateInfo()
        the_copy.admin_names = list(self.admin_names)
        the_copy.racer_names = list(self.racer_names)
        the_copy.match_info = self.match_info
        the_copy.race_info = raceinfo.RaceInfo.copy(self.race_info)
        return the_copy
