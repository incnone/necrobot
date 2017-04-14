LEVEL_UNKNOWN_DEATH = int(0)
LEVEL_NOS = int(-1)
LEVEL_FINISHED = int(-2)


# with level_str in the form x-y, returns the level as a number from 1 to 21, or -1 if invalid
def from_str(level_str):    
    args = level_str.split('-')
    if len(args) == 2:
        try:
            world = int(args[0])
            lvl = int(args[1])
            if (1 <= world <= 5 and 1 <= lvl <= 4) or (world == 5 and lvl == 5):
                return 4*(world-1) + lvl
        except ValueError:
            return -1
    return -1


# converts a level number from 1 to 21 into the appropriate x-y format; otherwise returns an empty string
def to_str(level):     
    if 1 <= level <= 21:
        world = min(((level-1) // 4) + 1, 5)
        lvl = level - 4*(world-1)
        return '{0}-{1}'.format(world, lvl)
    else:
        return ''


# returns an int that will cause this to sort correctly (replaces -2 with 999)
def level_sortval(level):
    if level == LEVEL_FINISHED:
        return 999
    else:
        return level