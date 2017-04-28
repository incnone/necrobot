from enum import IntEnum

LEVEL_UNKNOWN_DEATH = int(0)
LEVEL_NOS = int(-1)
LEVEL_FINISHED = int(-2)
LEVEL_MAX = 21
LEVELS_PER_ZONE = 4
TOTAL_ZONES = 5


# class LevelSpecial(IntEnum):
#     UNKNOWN_DEATH = 0,
#     NOS = -1,
#     FINISHED = -2
#
#
# class Level(object):
#     @staticmethod
#     def fromstr(level_str: str) -> int or None:
#         args = level_str.split('-')
#         if len(args) == 2:
#             try:
#                 zone = int(args[0])
#                 lvl = int(args[1])
#                 if (1 <= zone <= TOTAL_ZONES and 1 <= lvl <= LEVELS_PER_ZONE) or (zone == 5 and lvl == 5):
#                     return Level(zone=zone, level=lvl)
#             except ValueError:
#                 return None
#         return None
#
#     def __init__(
#             self,
#             zone: int = None,
#             level: int = None,
#             total_level: int = None,
#             level_special: LevelSpecial = None
#     ) -> None:
#         if total_level is not None:
#             self.zone = min(((total_level - 1) // LEVELS_PER_ZONE) + 1, TOTAL_ZONES)
#             self.level = total_level - LEVELS_PER_ZONE * (self.zone - 1)
#
#         self.zone = zone
#         self.level = level
#         self.level_special = level_special
#
#     def __int__(self) -> int:
#         if self.is_normal_level:
#             return 4*(self.zone - 1) + self.level
#         else:
#             return int(self.level_special)
#
#     def __str__(self) -> str:
#         if self.is_normal_level is None:
#             return '{0}-{1}'.format(self.zone, self.level)
#         elif self.is_normal_level == LevelSpecial.UNKNOWN_DEATH:
#             return 'unknown death'
#         elif self.is_normal_level == LevelSpecial.NOS:
#             return 'unknown'
#         elif self.is_normal_level == LevelSpecial.FINISHED:
#             return 'finished'
#
#     @property
#     def is_normal_level(self) -> bool:
#         return self.level_special is not None
#
#     def sortval(self, reverse: bool = False) -> int:
#         if self.level_special == LevelSpecial.FINISHED:
#             return LEVEL_MAX + 1
#         elif reverse:
#             return LEVEL_MAX - self.__int__() if self.__init__() > 0 else 0
#         else:
#             return self.__int__()


def from_str(level_str: str) -> int:
    """With level_str in the form x-y, return the level as a number from 1 to 21, or LEVEL_NOS if invalid"""
    args = level_str.split('-')
    if len(args) == 2:
        try:
            world = int(args[0])
            lvl = int(args[1])
            if (1 <= world <= TOTAL_ZONES and 1 <= lvl <= LEVELS_PER_ZONE) or (world == 5 and lvl == 5):
                return LEVELS_PER_ZONE*(world-1) + lvl
        except ValueError:
            return LEVEL_NOS
    return LEVEL_NOS


def to_str(level: int) -> str:
    """Convert a level number from 1 to 21 into the appropriate x-y format; otherwise return an empty string."""
    if 1 <= level <= LEVEL_MAX:
        world = min(((level-1) // LEVELS_PER_ZONE) + 1, TOTAL_ZONES)
        lvl = level - LEVELS_PER_ZONE*(world-1)
        return '{0}-{1}'.format(world, lvl)
    else:
        return ''


def level_sortval(level: int, reverse=False) -> int:
    """Return an int that will cause levels to sort correctly."""
    if level == LEVEL_FINISHED:
        return LEVEL_MAX + 1
    elif reverse:
        return LEVEL_MAX - level if level > 0 else level
    else:
        return level
