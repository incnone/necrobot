#with level_str in the form x-y, returns the level as a number from 1 to 17, or -1 if invalid
def from_str(level_str):    
    args = level_str.split('-')
    if len(args) == 2:
        try:
            world = int(args[0])
            lvl = int(args[1])
            if (world >= 1 and world <= 4 and lvl >= 1 and lvl <= 4) or (world == 4 and lvl == 5):
                return 4*(world-1) + lvl
        except ValueError:
            return -1
    return -1

#converts a level number from 1 to 17 into the appropriate x-y format; otherwise returns an empty string
def to_str(level):     
    if level >= 1 and level <= 17:
        world = min( ((level-1) // 4) + 1, 4)
        lvl = level - 4*(world-1)
        return '{0}-{1}'.format(world, lvl)
    else:
        return ''
