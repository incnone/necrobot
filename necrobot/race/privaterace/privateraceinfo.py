# Class holding info data for a private race.

from necrobot.race.race import raceinfo


# Attempts to parse the given command-line args into a race-info
# Returns the RacePrivateInfo on success, None on failure
# Warning: destroys information in the list args
def parse_args(args):
    race_private_info = PrivateRaceInfo()
    race_private_info.race_info = raceinfo.RaceInfo()
    race_private_info.race_info.can_be_solo = True
    race_private_info.race_info.post_results = False
    race_private_info.race_info.private_race = True
    raceinfo.parse_args_modify(args, race_private_info.race_info)
    if race_private_info.race_info is None:
        return None

    return race_private_info


class PrivateRaceInfo(object):
    @staticmethod
    def copy(private_race_info):
        the_copy = PrivateRaceInfo()
        the_copy.admin_names = list(private_race_info.admin_names)
        the_copy.racer_names = list(private_race_info.racer_names)
        the_copy.race_info = raceinfo.RaceInfo.copy(private_race_info.race_info)
        return the_copy

    def __init__(self):
        self.admin_names = []
        self.racer_names = []
        self.race_info = None
