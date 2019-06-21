"""
Essentially a config file, storing categories for the .submit command
"""

from necrobot.util import racetime

from typing import Optional, List
from necrobot.util.necrodancer.character import NDChar
from necrobot.race.raceinfo import RaceInfo


def get_raceinfo_for_keyword(keyword: str) -> Optional[RaceInfo]:
    # Change some default values for CoH
    race_info = RaceInfo()
    race_info.character = NDChar.Coh
    race_info.seeded = False
    race_info.amplified = False
    race_info.private_race = True

    # Keyword-specific values (custom descriptor)
    if keyword == 'story-any':
        race_info.descriptor = 'CoH: Story (any%)'
    elif keyword == 'story-nobs':
        race_info.descriptor = 'CoH: Story (all instruments)'
    elif keyword == 'permadeath':
        race_info.descriptor = 'CoH: Permadeath'
    elif keyword == 'doubletempo':
        race_info.descriptor = 'CoH: Double Tempo'
    elif keyword == 'fixedbeat':
        race_info.descriptor = 'CoH: Fixed Beat'
    else:
        return None

    return race_info


def convert_to_score(category_keyword: str, score: str) -> Optional[int]:
    time_categories = [
        'story-any',
        'story-nobs',
        'permadeath',
        'doubletempo'
    ]
    if category_keyword in time_categories:
        ret = racetime.from_str(score)
        if ret == -1:
            return None
        else:
            return ret
    elif category_keyword == 'fixedbeat':
        try:
            return int(score)
        except ValueError:
            return None
    else:
        return None


def convert_score_to_text(category_race_info_descriptor: str, score: int) -> Optional[str]:
    time_categories = [
        'CoH: Story (any%)',
        'CoH: Story (all instruments)',
        'CoH: Permadeath',
        'CoH: Double Tempo'
    ]
    if category_race_info_descriptor in time_categories:
        return racetime.to_str(score)
    elif category_race_info_descriptor == 'CoH: Fixed Beat':
        return str(score)
    else:
        return None


def category_list() -> List[str]:
    return [
        'story-any',
        'story-nobs',
        'permadeath',
        'doubletempo',
        'fixedbeat',
    ]
