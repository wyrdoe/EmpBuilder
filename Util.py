NUM_UNDERLING_TYPES = 4
NUM_UNDERLINGS_SHOP_TIER = 4
NUM_SHOP_TIERS = 2
NUM_UNDERLINGS = 5
NUM_MISSIONS_EACH = 5
NUM_MISSION_TYPES = 3
NUM_INITIAL_PLACEMENTS = 3
DEBUG_MODE = 0
VERBOSE = 1
from random import shuffle, randint
def isInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False
#UI:
#give user options
def selectionMaker(option_type, options):
    in_val = ''
    if len(options) == 0:
        return None
    if DEBUG_MODE:
        in_val = randint(0,len(options)-1)
    if VERBOSE and DEBUG_MODE:
        print in_val
    while not isInt(in_val) or int(in_val) < 0 or int(in_val) >= len(options) :
        astr = ['Please type the number of your selection of a {} from the following options:'.format(option_type)]
        for ind, opt in enumerate(options):
            astr.append('{}): {}'.format(ind,str(opt).strip()))
        if DEBUG_MODE and VERBOSE:
            print '\n'.join(astr)
        if not DEBUG_MODE:
            print '\n'.join(astr)
            in_val = raw_input()
    return options[int(in_val)]
def show_tiles(map_grid,tiles):
    lines = []
    for col in range(map_grid.map_dimension):
        line = [' '] if col % 2 else []
        for row in range(map_grid.map_dimension):
            tile = map_grid.map_tiles[row][col]
            if tile in tiles:
                line.append('{}X '.format(tile.terrain))
            else:
                line.append((tile.__repr__()))
        lines.append(' '.join(line))
    if VERBOSE:
        print '\n'.join(lines)
