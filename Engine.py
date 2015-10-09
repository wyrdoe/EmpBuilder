from random import shuffle, randint
from itertools import combinations

class Tile:
    def __init__(self,x,y,terrain):
        self.x = x
        self.y = y
        self.terrain = terrain if terrain != '.' else None
        self.neighbours = []
        self.owner = None
        self.citadel = 'C'
    def add_neighbour(self,neighbour):
        if neighbour.terrain != None and self.terrain != None:
            self.neighbours.append(neighbour)
        else:
            return False
        return True
    def get_neighbours(self):
        return self.neighbours
    def construct(self,player_num):
        if not self.owner and self.terrain != self.citadel:
            self.owner = player_num
            self.building_level = 1
        else:
            return False
        return True
    def get_owner(self):
        return self.owner
    def upgrade(self,player_num):
        if self.owner == player_num:
            self.building_level += 1
        else:
            return False
        return True
    def coords(self):
        return (self.x,self.y)
    def __repr__(self):
        return (self.terrain if self.terrain else '.') + (str(self.owner) + str(self.building_level) if self.owner != None else '  ')
        
class Map_grid:
    def __init__(self):
        with open('map.txt','r') as map_file:
            self.map_dimension = int(map_file.readline())
            self.map_tiles = [[0]*self.map_dimension for i in range(self.map_dimension)]
            for y, line in enumerate(map_file.read().split('\n')):
                for x, terrain in enumerate(line.strip().split(' ')):
                    self.map_tiles[x][y] = Tile(x, y, terrain)
                    for dir_y, dir_x in self.dirs_up_left(y):
                        self.add_mutual_neighbours(self.map_tiles[x][y],x+dir_x,y+dir_y)
    def __repr__(self):
        lines = [str(self.map_dimension)]
        for col in range(self.map_dimension):
            line = [' '] if col % 2 else []
            for row in range(self.map_dimension):
                line.append(str(self.map_tiles[row][col]))
            lines.append(' '.join(line))
        return '\n'.join(lines)
    
    #all_dirs = ((0,-1), (0,1), (-1,-1), (-1,0), (1,-1), (1,0))
    #all_dirs = ((0,-1), (0,1), (-1, 1), (-1,0), (1, 0), (1,1))
    def dirs_down_right(self,row):
        if row % 2 != 1:
            return ((0,1), (1,-1), (1,0))
        else:
            return ((0,1), (1, 0), (1,1))
    def dirs_up_left(self,row):
        if row % 2 != 1:
            return ((0,-1), (-1,0), (-1,-1))
        else:
            return ((0,-1), (-1,0), (-1, 1))
    def add_mutual_neighbours(self, tile_a,x,y):
        if x >= 0 and x < self.map_dimension and y >= 0 and y < self.map_dimension:
            tile_b = self.map_tiles[x][y]
            assert(tile_a.add_neighbour(tile_b) == tile_b.add_neighbour(tile_a))
    def coord_to_val(self,x,y):
        return y * self.map_dimension + x
    def val_to_coord(self,val):
        return val % self.map_dimension, val/self.map_dimension
    #Check if a list of sets contain any overlapping items
    def sets_overlap(self,list_of_sets):
        for i,a in enumerate(list_of_sets):
            for j,b in enumerate(list_of_sets):
                if i != j:
                    if any(k in a for k in b):
                        return True
        return False
    def find_max_number_groups(self,player_num,points):
        valid_combinations = self.find_groups_worth_points(player_num,points)
        for num in range(1,len(valid_combinations))[::-1]:
            for comb in combinations(valid_combinations,num):
                complimentary = True
                #check no tiles are used multiple times
                if not self.sets_overlap(comb):
                    return comb
        return None
    #find all subgroups which meet the points criteria #TODO do we want to test condition here too?
    def find_groups_worth_points(self,player_num,points):
        valid_combinations = []
        for group in self.connected_groups(player_num):
            #Minimum size is points / 2 since cities are worth 2 points
            for group_size in range((points+1)/2,points+1):
                for comb in combinations(group,group_size):
                    score = 0
                    for ind, val_a in enumerate(comb):
                        coord_a = self.val_to_coord(val_a)
                        score += self.map_tiles[coord_a[0]][coord_a[1]].building_level
                        if ind >= len(comb)-1:
                            conditions_met = score >= points
                        else:
                            conditions_met = False
                            for val_b in comb[ind+1:]:
                                coord_b = self.val_to_coord(val_b)
                                if self.map_tiles[coord_a[0]][coord_a[1]] in self.map_tiles[coord_b[0]][coord_b[1]].get_neighbours():
                                    conditions_met = True
                                    break
                        if not conditions_met:
                            break
                    if conditions_met:
                        valid_combinations.append(comb)
        return valid_combinations

    #return list of all connected groups belonging to one player
    def connected_groups(self,owner):
        found_groups = []
        for row, tile_row in enumerate(self.map_tiles):
            for col, tile in enumerate(tile_row):
                if tile.get_owner() == owner:
                    val = self.coord_to_val(row,col)
                    if not any((val in found_group for found_group in found_groups)):
                        group = set()
                        self.recurse_connections(tile,owner,group)
                        found_groups.append(group)
        return found_groups
    
    #find all connected settlements
    def recurse_connections(self,tile,owner,group_so_far):
        group_so_far.add(self.coord_to_val(*tile.coords()))
        for a_tile in tile.get_neighbours():
            if a_tile.get_owner() == owner and self.coord_to_val(*a_tile.coords()) not in group_so_far:
                self.recurse_connections(a_tile,owner,group_so_far)
                    
    def build_at(self,x,y,player_num):
        return self.map_tiles[x][y].construct(player_num)
    def upgrade_at(self,x,y,player_num):
        return self.map_tiles[x][y].upgrade(player_num)
        
class Mission():
    def __init__(self, line):
        line_split = line.strip().split(';')
        ind = 0
        self.mission_type   = line_split[0].strip().lower()
        self.num_groups     = line_split[1].strip()
        self.points         = line_split[2].strip()
        self.connected      = line_split[3].strip()
        self.name           = line_split[4].strip()
        self.condition_text = " ".join(line_split[5:]).strip()
        self.conditions = []
        for cond in self.condition_text.split(','):
            self.conditions.append(self.condition_parse(cond.strip()))
    def condition_parse(self, condition_text):
        #TODO return anonymous function that checks the condition
        return None
    def __repr__(self):
        return '{:6} {:4} {:4} {:4} {:20} {:4}'.format(self.mission_type, self.num_groups, self.points, self.connected, self.name, self.condition_text)
        
class Mission_factory():
    def __init__(self):
        with open('missions.txt','r') as mission_file:
            self.fields = mission_file.readline()
            self.all_missions = [[] for i in range(NUM_MISSION_TYPES)]
            self.mission_index = [0 for i in range(NUM_MISSION_TYPES)]
            mission_type_lookup = {'green':0,
                                   'blue':1,
                                   'red':2}
            for mission_num, line in enumerate(mission_file.read().split('\n')):
                a_mission = Mission(line)
                self.all_missions[mission_type_lookup[a_mission.mission_type]].append(a_mission)
            for i in range(NUM_MISSION_TYPES):
                shuffle(self.all_missions[i])
    def get_mission(self,mission_type=None):
        assert(sum(self.mission_index)<sum((len(mis) for mis in self.all_missions)))
        if mission_type != None:
            assert(self.mission_index[mission_type] < len(self.all_missions[mission_type]))
            
        while mission_type == None:
            mission_type = randint(0,NUM_MISSION_TYPES-1)
            if self.mission_index[mission_type] >= len(self.all_missions[mission_type]):
                mission_type = None
        self.mission_index[mission_type] += 1
        return self.all_missions[mission_type][self.mission_index[mission_type]-1]
    def __repr__(self):
        a_str = self.fields
        return a_str+'\n'.join((str(m) for mis in self.all_missions for m in mis))

class Underling_factory():
    def __init__(self):
        with open('underlings.txt','r') as underling_file:
            self.fields = underling_file.readline()
            self.all_underlings = [[] for i in range(NUM_UNDERLING_TYPES)]
            self.underling_index = [0 for i in range(NUM_UNDERLING_TYPES)]
            self.underling_type_lookup = {'start':0,
                                     'age1':1,
                                     'age2':2,
                                     'age3':3}
            for underling_num, line in enumerate(underling_file.read().split('\n')):
                a_underling = Underling(line)
                self.discard(a_underling)
            for i in range(NUM_UNDERLING_TYPES):
                shuffle(self.all_underlings[i])
    def get_underling(self, underling_type, underling_index=0):
        assert(underling_type < NUM_UNDERLING_TYPES)
        assert(underling_type == 0 or underling_index==0)
        if underling_type == 0:
            assert(underling_index < len(self.all_underlings[underling_type]))
            return self.all_underlings[underling_type][underling_index]
        else:
            if self.underling_index[underling_type] + 1 < len(self.all_underlings[underling_type]):
                self.underling_index[underling_type] += 1
                return self.all_underlings[underling_type][self.underling_index[underling_type]-1]
            else:
                return None
        if underlind_index == None:
            self.underling_index += 1      
    def __repr__(self):
        a_str = self.fields
        return a_str+'\n'.join((str(u) for und in self.all_underlings for u in und))
        #TODO
    #return an underling to the deck
    def discard(self,a_underling):
        self.all_underlings[self.underling_type_lookup[a_underling.underling_type]].append(a_underling)

class Underling():
    def __init__(self,line):
        line_split = line.strip().split(';')
        self.underling_type = line_split[0].strip().lower()
        self.cost     = line_split[1].strip()
        self.on_buy   = line_split[2].strip()
        self.on_pass  = line_split[3].strip()
        self.name     = line_split[4].strip()
        self.activate_text = " ".join(line_split[5:]).lower().strip()
        self.activations = []
        for act in self.activate_text.split(','):
            self.activations.append(self.activation_parse(act.strip()))
        self.reset()
    def __repr__(self):
        return '{:6} {:4} {:4} {:4} {:20} {}'.format(self.underling_type,self.cost,self.on_buy, self.on_pass, self.name,self.activate_text)
    def activation_parse(self,activate_text):
        pass
        #TODO
    def activate(self):
        success = False
        if not self.is_active:
            success = True
            #TODO
            self.position = -1
        return success
    def do_pass(self):
        success = False
        if self.position == 0:
            success = True
            #TODO
            self.position = 1
        return success
    def reset(self):
        self.position = 0
    def has_action(self):
        return self.position == 0
    
    
#Each player has a set of missions and a collection of underlings, they also have resource cubes
class Player:
    def __init__(self,player_number):
        self.player_number = player_number
        self.missions = []
        self.underlings = []
        self.resources = {'g':0,'w':0,'s':0}
    def __repr__(self):
        return 'player_number: {} Resources: {}\nMissions:\n{}\nUnderlings:\n{}'.format(self.player_number,self.resources,
                                                                       '\n'.join((str(m) for m in self.missions)),
                                                                       '\n'.join((str(u) for u in self.underlings)))
    def give_mission(self,a_mission):
        self.missions.append(a_mission)
    def give_underling(self,a_underling):
        self.underlings.append(a_underling)
    def replace_underling(self,a_underling,b_underling):
        try:
            ind = self.underlings.index(a_underling)
        except ValueError:
            assert(0)
        self.underlings[ind] = b_underling
    def new_round(self):
        for underling in self.underlings:
            underling.reset()
    #a player is passed when all underlings have been used
    def is_passed():
        for underling in self.underlings:
            if underling.has_action():
                return False
        return True

class Shop:
    def __init__(self, underling_factory):
        self.current_round = 0
        self.underling_factory = underling_factory
        self.shop_underlings = [[None for i in range(NUM_UNDERLINGS_SHOP_TIER)] for i in range(NUM_SHOP_TIERS)]        
    def __repr__(self):
        astr = []
        for i in range(NUM_SHOP_TIERS):
            astr.append('Underling Shop Tier {}'.format(i))
            astr += [str(und) for und in self.shop_underlings[i]]
        return '\n'.join(astr)
    def new_round(self, round_number):
        assert (round_number == self.current_round+1)
        self.current_round = round_number
        for und_index in range(NUM_UNDERLINGS_SHOP_TIER):
            for shop_tier in range(NUM_SHOP_TIERS)[::-1]:
                if shop_tier == NUM_SHOP_TIERS - 1:
                    if self.shop_underlings[shop_tier][und_index] != None:
                        self.underling_factory.discard(self.shop_underlings[shop_tier][und_index])
                else:
                    self.shop_underlings[shop_tier+1][und_index] = self.shop_underlings[shop_tier][und_index]
        age = self.check_age(round_number)
        self.shop_underlings[0] = [self.underling_factory.get_underling(age) for i in range(NUM_UNDERLINGS_SHOP_TIER)]
    def check_age(self, round_number):
        age = 0
        if round_number <= 4:
            age = 1
        elif round_number <= 7:
            age = 2
        else:
            age = 3
        return age

    def buy_underling(self,a_underling):
        for shop_tier in range(NUM_SHOP_TIERS):
            for und_index in range(NUM_UNDERLINGS_SHOP_TIER):
                if self.shop_underlings[shop_tier][und_index] == a_underling:
                    self.shop_underlings[shop_tier][und_index] = None
                    return a_underling
        for tier in self.shop_underlings:
            for underling in tier:
                if a_underling == underling:
                    return a_underling
        return None
                
        
class GameObject:
    def __init__(self,num_players):
        self.current_round = 0
        self.map_grid = Map_grid()
        self.mission_factory = Mission_factory()
        self.underling_factory = Underling_factory()
        self.shop = Shop(self.underling_factory)
        self.players = []
        for player_num in range(num_players):
            self.players.append(Player(player_num))
        assert(NUM_MISSIONS_EACH > NUM_MISSION_TYPES)
        #Give each player one mission of each type
        for mission_type in range(NUM_MISSION_TYPES):
            for a_player in self.players:
                a_player.give_mission(self.mission_factory.get_mission(mission_type))
        #Give each player the rest of their missions
        for mission in range(NUM_MISSIONS_EACH-NUM_MISSION_TYPES):
            for a_player in self.players:
                a_player.give_mission(self.mission_factory.get_mission())
        #Give players starting Underlings
        for underling in range(NUM_UNDERLINGS):
            for a_player in self.players:
                a_player.give_underling(self.underling_factory.get_underling(0,underling))
        self.new_round()
    def __repr__(self):
        return '\n'.join([str(self.map_grid),str(self.mission_factory),str(self.underling_factory),str(self.shop), '\n'.join((str(p) for p in self.players))])

    def new_round(self):
        self.current_round += 1
        self.shop.new_round(self.current_round)
        for player in self.players:
            player.new_round() 

NUM_UNDERLINGS_SHOP_TIER = 5
NUM_SHOP_TIERS = 2
NUM_UNDERLINGS = 5
NUM_UNDERLING_TYPES = 4
NUM_MISSIONS_EACH = 7
NUM_MISSION_TYPES = 3
if __name__ == "__main__":
    go = GameObject(2)
    
    go.map_grid.build_at(2,6,0)
    go.map_grid.build_at(1,6,0)
    go.map_grid.build_at(2,7,0)
    go.map_grid.build_at(3,7,0)
    go.map_grid.build_at(4,7,0)
    go.map_grid.build_at(5,6,0)
    go.map_grid.build_at(4,5,0)
    go.map_grid.build_at(3,5,0)
    go.map_grid.upgrade_at(3,7,0)
    go.map_grid.upgrade_at(4,5,0)

    go.shop.new_round(2)
    go.shop.new_round(3)
    go.shop.new_round(4)
    
    print go.map_grid
    for i,vals in enumerate(go.map_grid.find_max_number_groups(0,3)):
        print 'group {} found'.format(i),[go.map_grid.val_to_coord(val) for val in vals]

    
