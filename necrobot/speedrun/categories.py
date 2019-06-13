"""
Essentially a config file, storing categories for the .submit command
"""

from typing import Optional
from necrobot.race.raceinfo import RaceInfo


def get_raceinfo_for_keyword(keyword: str) -> Optional[RaceInfo]:
    if keyword == 'speed':
        return None
    elif keyword == 'score':
        return None
    else:
        return None
