from random import shuffle, randint
from itertools import combinations
from operator import add, sub
import sys

def isInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

class Tile:
    def __init__(self,x,y,terrain):
        self.x = x
        self.y = y
        self.terrain = terrain if terrain != '.' else None
        self.neighbours = []
        self.owner = None
        self.building_level = 0
        self.citadel = 'C'
    def add_neighbour(self,neighbour):
        if neighbour.terrain != None and self.terrain != None:
            self.neighbours.append(neighbour)
        else:
            return False
        return True
    def get_neighbours(self):
        return self.neighbours
    def is_buildable(self):
        return self.is_river_buildable() and not self.is_river()
    def is_river_buildable(self): #is river or buidable terrain
        return not (self.owner!=None or self.terrain == None or self.terrain == self.citadel)
    def same_terrain(self,tile):
        return self.terrain.lower() == tile.terrain.lower() if self.terrain and tile.terrain else False
    def construct(self,player_num):
        if self.is_river_buildable():
            self.owner = player_num
            self.building_level = 1
        else:
            return False
        return True
    def demolish(self,player_num):
        success = False
        if self.owner == player_num:
            self.owner = None
            self.building_level = 0
            success = True
        return success
    def upgrade(self,player_num):
        success = False
        if self.owner == player_num:
            self.building_level += 1
            success = True
        return success
    def is_shield(self):
        return self.terrain == 'G'
    def is_river(self):
        return self.terrain == 'o'
    def is_forest(self):
        return self.terrain == 'f'
    def is_mountain(self):
        return self.terrain == 'm'
    def is_desert(self):
        return self.terrain == 'd'
    def is_grassland(self):
        return self.terrain.lower() == 'g'
    def is_city(self):
        return self.building_level == 1
    def is_citadel(self):
        return self.terrain.lower() == 'c'
    def is_outer_citadel(self):
        return self.terrain == 'C'
    def get_owner(self):
        return self.owner
    def coords(self):
        return (self.x,self.y)
    def __repr__(self):
        return (self.terrain if self.terrain else '.') + (str(self.owner) + str(self.building_level) if self.owner != None else '  ')
    def __str__(self):
        return '{},{}: {}'.format(self.x,self.y,(self.terrain if self.terrain else '.'))
        
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
                line.append((self.map_tiles[row][col].__repr__()))
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
                        self.recurse_connections(tile,owner,lambda tile, owner: tile.get_owner() == own, group)
                        found_groups.append(group)
        return found_groups
    
    #find all connected settlements
    def recurse_connections(self,tile,owner,condition,group_so_far,dist=None):
        if dist == None or dist > 0:
            dist = dist - 1 if dist != None else None
            group_so_far.add(self.coord_to_val(*tile.coords()))
            for a_tile in tile.get_neighbours():
                #if a_tile.get_owner() == owner and self.coord_to_val(*a_tile.coords()) not in group_so_far:
                if condition(a_tile,owner) and self.coord_to_val(*a_tile.coords()) not in group_so_far:
                    self.recurse_connections(a_tile,owner,condition,group_so_far,dist)
    def build_at(self,x,y,player_num):
        return self.map_tiles[x][y].construct(player_num)
    def upgrade_at(self,x,y,player_num):
        return self.map_tiles[x][y].upgrade(player_num)
    def get_rivers(self):
        found_groups = []
        for row, tile_row in enumerate(self.map_tiles):
            for col, tile in enumerate(tile_row):
                if tile.is_river():
                    val = self.coord_to_val(row,col)
                    if not any((val in found_group for found_group in found_groups)):
                        group = set()
                        self.recurse_connections(tile,None,lambda tile, owner: tile.is_river(),group)
                        found_groups.append(group)
        return found_groups
    def get_buildable(self,owned_tiles,dist=None,terrain_agnostic=True, river_allowed=False,river_dist=0,citadel_only=False): #get_buildable(self.tiles,dist,terrain_agnostic,river_allowed,river_dist)
        if dist == None:
            return self.get_buildable_global(river_allowed,citadel_only)
        extra_tiles = set()
        river_buidable = set()
        if river_allowed:
            condition = lambda source_tile, dest_tile: dest_tile.is_river_buildable()
        elif not terrain_agnostic:
            condition = lambda source_tile, dest_tile: dest_tile.is_buildable() and source_tile.same_terrain(dest_tile)
        else:
            condition = lambda source_tile, dest_tile: dest_tile.is_buildable()
        
        for tile in owned_tiles:
            for a_tile in tile.get_neighbours():
                extra_tiles.add((tile,a_tile))
                if a_tile.is_river():
                    pass
##                    for i in range(river_dist-1):
##                        new_river = []
##                        #source_tile,dest_tile in
                        #todo RIVER
                    
        #really inefficient with large values of dist, but better than copying for small numbers which are the expected
        for i in range(dist-1): 
            new_extra = []
            for source_tile,dest_tile in extra_tiles:
                for a_tile in dest_tile.get_neighbours():
                    new_extra.append((source_tile,a_tile))
            for extra in new_extra:
                extra_tiles.add(extra)
        retval = set()
        for extra in extra_tiles:
            source_tile,dest_tile = extra
            dest_tile.is_buildable()
            source_tile.same_terrain(dest_tile)
            if condition(source_tile,dest_tile):
                retval.add(dest_tile)
        return list(retval)
    def get_buildable_global(self,river_allowed=False,citadel_only=False):
        if river_allowed and citadel_only:
            condition = lambda tile: tile.is_river_buildable() and any((True for t in tile.get_neighbours() if t.is_citadel()))
        elif river_allowed:
            condition = lambda tile: tile.is_river_buildable()
        elif citadel_only:
            condition = lambda tile: tile.is_buildable() and any((True for t in tile.get_neighbours() if t.is_citadel()))
        else:
            condition = lambda tile: tile.is_buildable()
        return [tile for tile_row in self.map_tiles for tile in tile_row if condition(tile)]

    def valid_initial_placement(self,player_num):
        ret_val = []
        for tile in self.get_buildable_global(river_allowed=False,citadel_only=True):
            for nt in tile.get_neighbours():
                if nt.is_outer_citadel():
                    if not any((citadel_neighbour.owner == player_num for citadel_neighbour in nt.get_neighbours())):
                        ret_val.append(tile)
        return ret_val
        
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
            for i in range(1,NUM_UNDERLING_TYPES):
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
        self.line = line
        line_split = line.strip().split(';')
        self.underling_type = line_split[0].strip().lower()
        self.cost     = self.transient_resource_parse(line_split[1])
        self.on_buy   = line_split[2].strip()
        self.pass_reward  = [self.transient_resource_parse(reward_str) for reward_str in line_split[3].strip().split('|')]
        self.name     = line_split[4].strip()
        self.activate_text = " ".join(line_split[5:]).lower().strip()
        #self.activations = []
        #for act in self.activate_text.split(','):
        #    self.activations.append(self.activation_parse(act.strip()))
        self.reset()
    def copy(self):
        return Underling(self.line)
    def __repr__(self):
        return '{:6} {:4} {:4} {:4} {:20} {}'.format(self.underling_type,self.cost,self.on_buy, self.pass_reward, self.name,self.activate_text)
    def activation_parse(self,activate_text):
        pass
        #TODO
    def activate(self,owner):
        success = False
        if self.position == 0:
            success = True
            tile = None
            for ind, action in enumerate(self.activate_text.split(',')):
                #do one action, and then if sucessful, do further actions
                if success:
                    #an act may be split up into several options choose one:
                    if '|' in action:
                        action = selectionMaker('action to perform',action.split('|'))
                    new_success,tile = self.do_act(action.strip(),owner,tile)
                    if ind == 0:
                        success = new_success
            if success:
                self.position = -1
        return success
    def do_pass(self):
        reward = []
        if self.position == 0:
            reward = self.pass_reward
            self.position = 1
        return reward
    def transient_resource_parse(self,parse_str):
        parse_str_stripped = parse_str.strip().lower()
        crystal = 0
        if parse_str_stripped.endswith('c'):
            crystal = 1
            parse_str_stripped = parse_str_stripped[:-1]
        assert(isInt(parse_str_stripped))
        return int(parse_str_stripped),crystal
        
    def reset(self):
        self.position = 0
    def has_action(self):
        return self.position == 0

    def do_act(self,act,owner,tile=None):
        success = False
        act = act.split(' ')
        ind = 0
        if act[ind] == 'build':
            ind += 1
            resources = []
            for cost in act[ind].split('+'):
                resources += self.resource_parse(owner,cost,'Spent Resource')
            resource_cost = self.resource_combine(resources)
            ind += 1
            buildable_tiles = []
            dist = 1
            river_allowed = False
            river_dist = 0
            citadel_only = False
            terrain_agnostic = True
            if len(act) > ind:
                if act[ind] == 'river':
                    river_allowed = True
                    river_dist = None
                    ind += 1
                elif act[ind] == 'water':
                    river_dist = int(act[ind+1])
                    ind += 2
                elif act[ind] == 'citadel':
                    citadel_only = True
                    dist = None
                    ind += 1
                elif act[ind] == 'anywhere':
                    ind += 1
                    dist = None
                elif act[ind] == 'cross':
                    terrain_agnostic = False
                    
            #Add basic cost tiles:
            if all((owner.check_resources(rc) for rc in resource_cost)):
                buildable_tiles = [(tile, resource_cost) for tile in owner.get_buildable(dist,terrain_agnostic,river_allowed,river_dist,citadel_only)]
            if len(act) > ind:
                if act[ind] == 'jump':
                    dist +=1
                    ind += 1
                elif act[ind] == 'cross':
                    terrain_agnostic = True
                    ind += 1                        
                for cost in act[ind].split('+'):
                    resources += self.resource_parse(owner,cost,'Additional Resource')
                ind += 1
                resource_cost = self.resource_combine(resources)
            if all((owner.check_resources(rc) for rc in resource_cost)):
                buildable_tiles += [(tile, resource_cost) for tile in owner.get_buildable(dist,terrain_agnostic,river_allowed,river_dist,citadel_only)]
            #Add further cost tiles:
            
            if len(buildable_tiles) == 0:
                success = False
            else:
                if len(buildable_tiles) > 1:
                    tile,cost = selectionMaker('Settlement to build',buildable_tiles)
                else:
                    tile,cost = buildable_tiles[0]
                success = owner.give_tile(tile)
            if success:
                assert(all((owner.take_resources(rc) for rc in cost)))
                                     
        elif act[ind] == 'gain':
            #TODO non-int income
            rewards = act[ind+1]
            ind += 2
            success = True
            max_val_allowed = None
            if len(act) > ind:
                if act[ind] == 'shield':
                    success = False
                    if tile == None:
                        #We haven't specified a tile this means any tile we own
                        tiles = owner.get_tiles()
                    else:
                        tiles = [tile]
                    success = any((tt.is_shield() for tt in tiles))
                if act[ind] == 'max':
                    ind += 1
                    max_val_allowed = int(act[ind])
                ind += 1
            if success:
                resources = []
                for reward in rewards.split('+'):
                    resources += self.resource_parse(owner,reward,'Income Resource')
                for res_quant in self.resource_combine(resources,max_val_allowed):
                    owner.give_resources(res_quant)

        elif act[ind] =='upgrade':
            #TODO move
            ind += 1
            resources = []
            for cost in act[ind].split('+'):
                resources += self.resource_parse(owner,cost,'Spent Resource')
            resource_cost = self.resource_combine(resources)
            ind += 1
            if all((owner.check_resources(rc) for rc in resource_cost)):
                all_settlements = owner.get_settlements_only()
                if len(all_settlements) == 0:
                    success = False
                else:
                    if len(all_settlements) > 1:
                        tile = selectionMaker('Settlement to Upgrade',all_settlements)
                    else:
                        tile = all_settlements[0]
                    success = tile.upgrade(owner.player_number)
                if success:
                    assert(all((owner.take_resources(rc) for rc in resource_cost)))
                                     
        elif act[ind] =='score':
            assert(isInt(act[ind+1]))
            reward = int(act[ind+1])
            ind += 2
            
            success = True
            if len(act) > ind:
                success = act[ind] == 'shield' and tile != None and tile.is_shield()
            if success:
                owner.give_score(reward)
                                     
        elif act[ind] == 'move':
            ind += 1
            all_tiles = []
            source_tile = selectionMaker('Settlement to Move', ['None'] + [t for t in owner.get_tiles() if t != tile])
            if source_tile == 'None':
                success = False
            else:
                if act[ind] == 'here':
                    assert(tile != None)
                    all_tiles = [t for t in tile.get_neighbours() if t.is_buildable()]
                    ind += 1
                elif act[ind] == 'owned':
                    all_tiles = owner.get_buildable_sans_tile(source_tile,dist=1,terrain_agnostic=True,river_allowed=False,river_dist=0)
                    ind += 1
                elif act[ind] == 'anywhere':
                    all_tiles = owner.get_buildable(dist=None,terrain_agnostic=True,river_allowed=False,river_dist=0,citadel_only=False)
                    ind += 1
                
                dest_tile = selectionMaker('Movement Destination',all_tiles)
                success = owner.move_tile(source_tile,dest_tile)
        elif act[ind] == 'exchange':
            ind += 1
            resources = []
            for cost in act[ind].split('+'):
                resources += self.resource_parse(owner,cost,'Spent Resource',optional=True)
            resource_cost = self.resource_combine(resources)
            total_cost = sum((cost for resource, cost in resource_cost))
            ind += 1
            print 'exchange',resource_cost, total_cost,[owner.check_resources(rc) for rc in resource_cost]
            if all((owner.check_resources(rc) for rc in resource_cost)) and total_cost > 0:
                owner.give_score(total_cost)
                success = True
            if success:
                assert(all((owner.take_resources(rc) for rc in resource_cost)))
        #TODO option to use less than all
        elif act[ind] == 'trade':
        #TODO
            pass
        else:
            pass
        if ind != len(act):
            print self,ind, act
            assert(0)
        return success,tile

    #return a list of required resources
    def resource_parse(self,owner,to_parse,choice_message,optional=False):
        if isInt(to_parse[0]):
            quantity = int(to_parse[0])
        else:
            if to_parse[0] == 'f': #number of forests
                condition = lambda tile: tile.is_forest()
            elif to_parse[0] == 'm':#number of mountains
                condition = lambda tile: tile.is_mountain()
            elif to_parse[0] == 'S': #number of shields
                condition = lambda tile: tile.is_shield()
            elif to_parse[0] == 'C': #number of citadels
                condition = lambda tile: any((neighbour_tile.is_citadel() for neighbour_tile in tile.get_neighbours()))
            elif to_parse[0] == 'x': #number of cities
                condition = lambda tile: tile.is_city()
            quantity = owner.count_tiles(condition)
        if len(to_parse) == 2:
            ret_val = [to_parse[1]]*quantity
        else:
            ret_val = []
            for i in range(quantity):
                nothing = 'Nothing'
                selection = selectionMaker(choice_message,list(to_parse[1:])+([nothing] if optional else []))
                if selection == nothing:
                    break
                ret_val.append(selection)
        return ret_val
    def resource_combine(self,resources,max_val_allowed=None):
        resources.sort()
        ret_val = []
        if len(resources) > 0:
            quant = 1
            prev = resources[0]
            for res in resources[1:]:
                if res == prev:
                    quant = quant + 1 if max_val_allowed == None else min(quant + 1,max_val_allowed)
                else:
                    ret_val.append((prev,quant))
                    quant = 1
                    prev = res
            ret_val.append((prev,quant))
        return ret_val
    
#Each player has a set of missions and a collection of underlings, they also have resource cubes
class Player:
    def __init__(self,player_number,shop,map_grid):
        self.player_number = player_number
        self.map = map_grid
        self.shop = shop
        self.missions = []
        self.underlings = []
        self.resources = {'g':0,'w':0,'s':0}
        self.tiles = []
        self.score = 0
    def __repr__(self):
        return 'player_number: {} Resources: {} Score: {}\nMissions:\n{}\nUnderlings:\n{}'.format(self.player_number,self.resources,
                                                                       self.score, '\n'.join((str(m) for m in self.missions)),
                                                                       '\n'.join((str(u) for u in self.underlings)))
    def give_tile(self,tile):
        success = tile.construct(self.player_number)
        if success:
            self.tiles.append(tile)
        return success
    def move_tile(self,source_tile,dest_tile):
        success = self.give_tile(dest_tile)
        if success:
            while source_tile.building_level > dest_tile.building_level:
                dest_tile.upgrade(self.player_number)
            assert(self.remove_tile(source_tile))
        return success
    def remove_tile(self,tile):
        success = tile.demolish(self.player_number)
        if success:
            self.tiles.remove(tile)
        return success
    def get_settlements_only(self):
        return [tile for tile in self.tiles if tile.building_level == 1]
    def get_tiles(self):
        return self.tiles
    def count_tiles(self, condition):
        return sum([1 for tile in self.tiles if condition(tile)])
    def give_resources(self,resource_quantity):
        resource,quantity = resource_quantity
        self.resources[resource] += quantity
    def check_resources(self,resource_quantity):
        resource,quantity = resource_quantity
        return self.resources[resource] >= quantity
    def take_resources(self,resource_quantity):
        resource,quantity = resource_quantity
        success = False
        if self.check_resources(resource_quantity):
            self.resources[resource] -= quantity
            success = True
        return success
    def give_score(self,quantity):
        self.score += quantity
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
    def is_passed(self):
        for underling in self.underlings:
            if underling.has_action():
                return False
        return True
    def use_underling(self,underling_pos):
        return self.underlings[underling_pos].activate(self)
    def get_buildable(self,dist,terrain_agnostic=True,river_allowed=False,river_dist=0,citadel_only=False):
        return self.map.get_buildable(self.tiles,dist,terrain_agnostic,river_allowed,river_dist,citadel_only)
    def get_buildable_sans_tile(self,tile,dist,terrain_agnostic=True,river_allowed=False,river_dist=0,citadel_only=False):
    #used to remove one tile from consideration
        return self.map.get_buildable([t for t in self.tiles if t != tile],dist,terrain_agnostic,river_allowed,river_dist,citadel_only)                                
    def do_pass(self):
        rewards = [(0,0)]
        for underling in self.underlings:
            if underling.has_action():
                new_reward = []
                for rward in underling.do_pass():
                    for reward in rewards:
                        new_reward.append([sum(x) for x in zip(rward, reward)])
                rewards = new_reward
        pass_choices = set()
        for reward in rewards:
            for cc in self.shop.affordable(reward):
                pass_choices.add(cc)
        selected = selectionMaker('Purchase',list(pass_choices))
        self.shop.purchase(selected,self)
    #give user options

def selectionMaker(option_type, options):
    in_val = ''
    while not isInt(in_val) or int(in_val) < 0 or int(in_val) >= len(options) :
        print 'Please type the number of your selection of a {} from the following options:'.format(option_type)
        for ind, opt in enumerate(options):
            print '{}): {}'.format(ind,str(opt).strip())
        in_val = raw_input()
    return options[int(in_val)]
        
    
class Shop:
    def __init__(self, underling_factory):
        self.current_round = 0
        self.underling_factory = underling_factory
        self.shop_underlings = [[None for i in range(NUM_UNDERLINGS_SHOP_TIER)] for i in range(NUM_SHOP_TIERS)]
        self.resource_shop = {'stone':{'name':'s','quantity':1,'cost':(1,0)},'wood':{'name':'w','quantity':1,'cost':(1,0)},'gold':{'name':'g','quantity':1,'cost':(2,0)}}
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
    #return the currently affordable underlings and resources
    def affordable(self,reward):
        affordable_list = []
        for resource, resource_dict in self.resource_shop.items():
            if all((val >= 0 for val in map(sub,reward,resource_dict['cost']))):
                affordable_list.append(resource)
        for shop_tier in range(NUM_SHOP_TIERS):
            discount = (shop_tier+1,0)
            for und in self.shop_underlings[shop_tier]:
                if und != None:
                    if all((val >= 0 for val in map(sub,map(add,discount,reward),und.cost))):
                        affordable_list.append(und)
        return affordable_list            
        
    def purchase(self,purchase_selection,owner):        
        if purchase_selection in self.resource_shop:
            owner.give_resources((self.resource_shop[purchase_selection]['name'],self.resource_shop[purchase_selection]['quantity']))
            return True
        for shop_tier in range(NUM_SHOP_TIERS):
            for und_index in range(NUM_UNDERLINGS_SHOP_TIER):
                if self.shop_underlings[shop_tier][und_index] == purchase_selection:
                    self.shop_underlings[shop_tier][und_index] = None
                    owner.give_underling(purchase_selection)
                    purchase_selection.do_pass()
                    return True
        return False
                
        
class GameObject:
    def __init__(self,num_players):
        self.current_round = 0
        self.map_grid = Map_grid()
        self.mission_factory = Mission_factory()
        self.underling_factory = Underling_factory()
        self.shop = Shop(self.underling_factory)
        self.players = []
        for player_num in range(num_players):
            self.players.append(Player(player_num,self.shop,self.map_grid))
            self.players[player_num].give_resources(('w',1))
            self.players[player_num].give_resources(('s',1))
            self.players[player_num].give_resources(('g',1))
        assert(NUM_MISSIONS_EACH > NUM_MISSION_TYPES)
        #Give each player one mission of each type
        for mission_type in range(NUM_MISSION_TYPES):
            for a_player in self.players:
                a_player.give_mission(self.mission_factory.get_mission(mission_type))
        #Give each player the rest of their missions
        for mission in range(NUM_MISSIONS_EACH-NUM_MISSION_TYPES):
            for a_player in self.players:
                a_player.give_mission(self.mission_factory.get_mission())
        #Give players a copy of the starting Underlings
        for underling in range(NUM_UNDERLINGS):
            for a_player in self.players:
                a_player.give_underling(self.underling_factory.get_underling(0,underling).copy())
        self.start_player = randint(0,num_players-1)
        self.current_player = self.start_player
    def __repr__(self):
        return '\n'.join([str(self.map_grid),str(self.mission_factory),str(self.underling_factory),str(self.shop), '\n'.join((str(p) for p in self.players))])

    def all_players_passed(self):
        return all((player.is_passed() for player in self.players))

    def new_round(self):
        self.current_round += 1
        self.shop.new_round(self.current_round)
        for player in self.players:
            player.new_round()
        self.start_player = (self.start_player + 1)%len(self.players)
        self.current_player = self.start_player
    def next_player(self, clockwise=True):
        delta = 1 if clockwise else -1 + len(self.players)
        self.current_player = (self.current_player + delta)%len(self.players)
        while self.players[self.current_player].is_passed():
            self.current_player = (self.current_player + delta)%len(self.players)
        return self.current_player
    def get_current_player(self):
        return self.players[self.current_player]
    def place_initial_settlements(self):
        for i in range(NUM_INITIAL_PLACEMENTS):
            if i % 2 == 0:
                clockwise = True
            else:
                clockwise = False
            for j in range(len(self.players)):
                all_tiles = self.map_grid.valid_initial_placement(self.current_player)
                selection = selectionMaker('Player {} Initial Placement'.format(self.current_player),all_tiles)
                self.get_current_player().give_tile(selection)
                self.next_player(clockwise)
            self.next_player(not clockwise)
            
        

NUM_UNDERLINGS_SHOP_TIER = 5
NUM_SHOP_TIERS = 2
NUM_UNDERLINGS = 5
NUM_UNDERLING_TYPES = 4
NUM_MISSIONS_EACH = 7
NUM_MISSION_TYPES = 3
NUM_INITIAL_PLACEMENTS = 3
if __name__ == "__main__":
    num_players = 3
    go = GameObject(num_players)
    
    #go.map_grid.build_at(2,6,0)
    #go.map_grid.build_at(1,6,0)
    #go.map_grid.build_at(2,7,0)
    #go.map_grid.build_at(3,7,0)
    #go.map_grid.build_at(4,7,0)
    #go.map_grid.build_at(5,6,0)
    #go.map_grid.build_at(4,5,0)
    #go.map_grid.build_at(3,5,0)
    #go.map_grid.upgrade_at(3,7,0)
    #go.map_grid.upgrade_at(4,5,0)

    #go.players[0].give_resources(('s',9))
    #go.players[0].give_resources(('g',9))
    #go.players[0].give_resources(('w',6))
    #go.players[0].give_tile(go.map_grid.map_tiles[2][6])
    #go.players[0].give_tile(go.map_grid.map_tiles[1][6])
    #go.players[0].give_tile(go.map_grid.map_tiles[2][7])
    #go.players[0].give_tile(go.map_grid.map_tiles[3][7])
    #go.players[0].give_tile(go.map_grid.map_tiles[4][7])
    #go.players[0].give_tile(go.map_grid.map_tiles[5][6])
    #go.players[0].give_tile(go.map_grid.map_tiles[4][5])
    #go.players[0].give_tile(go.map_grid.map_tiles[3][5])

    #print go.map_grid.get_rivers()

    for round_number in range(1,10):
        
        print go.map_grid
        underling_name = ''
        current_player = go.get_current_player().player_number
        go.place_initial_settlements()
        print go.map_grid
        go.new_round()
        while not go.all_players_passed():
            print 'Player {} Turn'.format(current_player)
            underling_name = selectionMaker('Underling to Activate',['Pass','Display Map','Display Shop','Display Player']+[und.name for und in go.get_current_player().underlings if und.has_action()]+['Exit'])
            success = False
            if underling_name == 'Exit':
                sys.exit(0)
            elif underling_name == 'Pass':
                success = go.get_current_player().do_pass()
                current_player = go.next_player()
            elif underling_name == 'Display Map':
                print go.map_grid
            elif underling_name == 'Display Player':
                print go.players[current_player]
            elif underling_name == 'Display Shop':
                print go.shop
            else:
                for ind, a_underling in enumerate(go.get_current_player().underlings):
                    if a_underling.name == underling_name:
                        success = go.get_current_player().use_underling(ind)
                        break
                if success:
                    current_player = go.next_player()
                else:
                    print 'action {}, failed'.format(underling_name)
            #if success:
                #print go.players[0]
        
        
        #mg = go.map_grid.find_max_number_groups(0,3)
        #if mg:
        #    for i,vals in enumerate(mg):
        #        print 'group {} found'.format(i),[go.map_grid.val_to_coord(val) for val in vals]
    

#TODO Missions, score round, selection of active underlings, choice of spending only when options exist, building, moving

    
