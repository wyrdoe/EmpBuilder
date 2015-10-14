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
    def get_buildable(self,owned_tiles,dist=None,terrain_agnostic=True, river_allowed=False,river_dist=0): #get_buildable(self.tiles,dist,terrain_agnostic,river_allowed,river_dist)
        if dist == None:
            return get_buildable_global(self,river_allowed)
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
        for extra in extra_tiles.copy():
            source_tile,dest_tile = extra
            dest_tile.is_buildable()
            source_tile.same_terrain(dest_tile)
            if not condition(source_tile,dest_tile):
                extra_tiles.remove(extra)
        return [dest_tile for source_tile, dest_tile in extra_tiles]
    def get_buildable_global(self,river_allowed=False):
        if river_allowed:
            condition = lambda tile: tile.is_river_buildable()
        else:
            condition = lambda tile: tile.is_buildable()
        return [tile for tile_row in self.map_tiles for tile in tile_row if condition(tile)]        
        
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
            for action in self.activate_text.split(','):
                #do one action, and then if sucessful, do further actions
                if success:
                    #an act may be split up into several options choose one:
                    if '|' in action:
                        action = selectionMaker('action to perform',action.split('|'))
                    success,tile = self.do_act(action.strip(),owner,tile)
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
                resources += self.resource_parse(cost,'Spent Resource')
            resource_cost = self.resource_combine(resources)
            ind += 1
            buildable_tiles = []
            dist = 1
            same_river = False
            river_dist = 0
            citadel = False
            terrain_agnostic = True
            if len(act) > ind:
                if act[ind] == 'river':
                    same_river = True
                    ind += 1
                elif act[ind] == 'citadel':
                    citadel = True
                    dist = 0
                    ind += 1
                elif act[ind] == 'anywhere':
                    ind += 1
                    dist = None
                elif act[ind] == 'cross':
                    terrain_agnostic = False
            #Add basic cost tiles:
            if all((owner.check_resources(rc) for rc in resource_cost)):
                buildable_tiles = [(tile, resource_cost) for tile in owner.get_buildable(dist,terrain_agnostic,same_river,river_dist)]
            if len(act) > ind:
                if act[ind] == 'jump':
                    dist +=1
                    ind += 1
                elif act[ind] == 'cross':
                    terrain_agnostic = True
                    ind += 1                        
                for cost in act[ind].split('+'):
                    resources += self.resource_parse(cost,'Additional Resource')
                ind += 1
                resource_cost = self.resource_combine(resources)
            if all((owner.check_resources(rc) for rc in resource_cost)):
                buildable_tiles += [(tile, resource_cost) for tile in owner.get_buildable(dist,terrain_agnostic,same_river,river_dist)]
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
            
            #TODO all
        elif act[ind] == 'gain':
            #TODO non-int income
            rewards = act[ind+1]
            ind += 2
            success = True
            if len(act) > ind:
                success = False
                if tile == None:
                    #We haven't specified a tile this means any tile we own
                    tiles = owner.get_tiles()
                else:
                    tiles = [tile]
                if act[ind] == 'shield':
                    success = any((tt.is_shield() for tt in tiles))
                ind += 1
            if success:
                resources = []
                for reward in rewards.split('+'):
                    resources += self.resource_parse(reward,'Income Resource')
                for res_quant in self.resource_combine(resources):
                    owner.give_resources(res_quant)
        elif act[ind] =='upgrade':
            #TODO move
            ind += 1
            resources = []
            for cost in act[ind].split('+'):
                resources += self.resource_parse(cost,'Spent Resource')
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
                owner.score += reward
        else:
            pass
        if ind != len(act):
            print self,ind, act
            assert(0)
        return success,tile

    #return a list of required resources
    def resource_parse(self,to_parse,choice_message):
        if isInt(to_parse[0]):
            quantity = int(to_parse[0])
        else:
            pass
            #TODO nonnumerical quantity
        if len(to_parse) == 2:
            ret_val = [to_parse[1]]*quantity
        else:
            ret_val = []
            for i in range(quantity):
                ret_val.append(selectionMaker(choice_message,list(to_parse[1:])))
        return ret_val
    def resource_combine(self,resources):
        resources.sort()
        ret_val = []
        if len(resources) > 0:
            quant = 1
            prev = resources[0]
            for res in resources[1:]:
                if res == prev:
                    quant += 1
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
    def __repr__(self):
        return 'player_number: {} Resources: {}\nMissions:\n{}\nUnderlings:\n{}'.format(self.player_number,self.resources,
                                                                       '\n'.join((str(m) for m in self.missions)),
                                                                       '\n'.join((str(u) for u in self.underlings)))
    def give_tile(self,tile):
        success = tile.construct(self.player_number)
        if success:
            self.tiles.append(tile)
        return success
    def move_tile(self,a_tile,b_tile):
        success = self.give_tile(b_tile)
        if success:
            while a_tile.building_level > b_tile.building_level:
                b_tile.upgrade(self.player_number)
            assert(self.remove_tile(a_tile))
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
    def get_buildable(self,dist,terrain_agnostic=True,same_river=False,river_dist=0):
        river_allowed = same_river
        #todo add in same_river
        return self.map.get_buildable(self.tiles,dist,terrain_agnostic,river_allowed,river_dist)
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
            print '{}): {}'.format(ind,opt)
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

    go.players[0].give_resources(('s',9))
    go.players[0].give_resources(('g',9))
    go.players[0].give_resources(('w',6))
    go.players[0].give_tile(go.map_grid.map_tiles[2][6])
    go.players[0].give_tile(go.map_grid.map_tiles[1][6])
    go.players[0].give_tile(go.map_grid.map_tiles[2][7])
    #go.players[0].give_tile(go.map_grid.map_tiles[3][7])
    #go.players[0].give_tile(go.map_grid.map_tiles[4][7])
    #go.players[0].give_tile(go.map_grid.map_tiles[5][6])
    #go.players[0].give_tile(go.map_grid.map_tiles[4][5])
    #go.players[0].give_tile(go.map_grid.map_tiles[3][5])

    #print go.map_grid.get_rivers()

    for round_number in range(1,10):
        go.new_round()
        print go.map_grid
        underling_name = ''
        while not go.players[0].is_passed():
            underling_name = selectionMaker('Underling to Activate',['Pass','Display Map','Display Shop','Display Player']+[und.name for und in go.players[0].underlings if und.has_action()]+['Exit'])
            success = False
            if underling_name == 'Exit':
                sys.exit(0)
            elif underling_name == 'Pass':
                success = go.players[0].do_pass()
            elif underling_name == 'Display Map':
                print go.map_grid
            elif underling_name == 'Display Player':
                print go.players[0]
            elif underling_name == 'Display Shop':
                print go.shop
            else:
                for ind, a_underling in enumerate(go.players[0].underlings):
                    if a_underling.name == underling_name:
                        success = go.players[0].use_underling(ind)
            #if success:
                #print go.players[0]
        
        
        #mg = go.map_grid.find_max_number_groups(0,3)
        #if mg:
        #    for i,vals in enumerate(mg):
        #        print 'group {} found'.format(i),[go.map_grid.val_to_coord(val) for val in vals]
    

#TODO Missions, score round, selection of active underlings, choice of spending only when options exist, building, moving

    
