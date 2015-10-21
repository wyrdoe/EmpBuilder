from random import shuffle, randint

from operator import add, sub
import sys
from Util import *
from MapGrid import Tile, Map_grid
from Underlings import Underling, Underling_factory
from collections import defaultdict
        
class Mission():
    def __init__(self, line):
        line_split = line.strip().split(';')
        ind = 0
        self.mission_type   = line_split[0].strip().lower()
        self.num_groups     = int(line_split[1].strip())
        self.points         = int(line_split[2].strip())
        self.connected      = int(line_split[3].strip())
        self.name           = line_split[4].strip()
        self.condition_text = " ".join(line_split[5:]).strip()
        self.conditions = []
    def __repr__(self):
        return '{:6} {:4} {:4} {:4} {:20} {:4}'.format(self.mission_type, self.num_groups, self.points, self.connected, self.name, self.condition_text)
    def check_condition(self, map_grid, group):
        success = True
        for condition in self.condition_text.split(', '):
            cond = condition.split(' ')
            ind = 0
            #GREEN
            terrain_required = defaultdict(int)
            comb_info = defaultdict(int)
            for terrain in terrain_required.keys():
                if terrain == cond[ind]:
                    terrain_required[terrain] = cond[ind+1]
                    ind += 1
            for tile in group:
                comb_info['grass'] += tile.is_grassland()
                comb_info['not_grass'] += not tile.is_grassland()
                comb_info['desert'] += tile.is_desert()
                comb_info['not_desert'] += not tile.is_desert()
                comb_info['mountain'] += tile.is_mountain()
                comb_info['not_mountain'] += not tile.is_mountain()
                comb_info['forest'] += tile.is_forest()
                comb_info['not_forest'] += not tile.is_forest()
            for terrain in comb_info.keys():
                if terrain == cond[ind]:
                    if comb_info[terrain] < int(cond[ind+1]):
                        success = False
                    ind+=2
                    break
            if ind < len(cond) and cond[ind] == 'terrain':
                ind += 1
                terrains = ['grass','desert','mountain','forest']
                if cond[ind] == 'same':
                    ind += 1
                    success = sum((1 for key in terrains if comb_info[key] > 0)) == 1
                elif cond[ind] == 'different':
                    ind += 1
                    success = sum((1 for key in terrains if comb_info[key] > 1)) == 0
                else:
                    val = int(cond[ind])
                    success = sum((1 for key in terrains if comb_info[key] > 0)) >= val
                    ind += 1

            if ind < len(cond) and cond[ind] == 'river':
                ind += 1
                if cond[ind] == 'same':
                    ind += 1
                    success = False
                    for river_neighbours in map_grid.get_river_neighbours():
                        success |= all((tile in river_neighbours for tile in group))
                elif cond[ind] == 'none':
                    ind += 1
                    success = not any((neighbour.is_river() for tile in group for neighbour in tile.get_neighbours()))

            if ind < len(cond) and cond[ind] == 'city':
                ind += 1
                if cond[ind] == 'shield':
                    ind += 1
                    success = any((tile.is_city() and tile.is_shield() for tile in group))
                elif cond[ind] == 'opponent_city':
                    ind += 1
                    success = any((neighbour.is_city() and neighbour.get_owner() != tile.get_owner() for tile in group for neighbour in tile.get_neighbours() if tile.is_city()))
                else:
                    #number of cities
                    val = int(cond[ind])
                    ind += 1
                    city_count = sum((1 for tile in group if tile.is_city()))
                    success = city_count >= val
                    
            if ind < len(cond) and cond[ind] == 'citadel':
                ind += 1
                if cond[ind] == 'touch':
                    ind += 1
                    success = any((neighbour.is_citadel() for tile in group for neighbour in tile.get_neighbours()))
                elif cond[ind] == 'share':
                    ind += 1
                    success = False
                    for tile in group:
                        for neighbour in tile.get_neighbours():
                            if neighbour.is_citadel():
                                for neighbour_2 in neighbour.get_neighbours():
                                    if neighbour_2.get_owner() != tile.get_owner():
                                        success = True
                                        break
                            if success:
                                break
                        if success:
                            break
                    
            if ind < len(cond) and cond[ind] == 'shape':
                ind += 1
                if cond[ind] == 'triangle':
                    ind += 1
                    success = False
                    #TODO later, may have been removed
                elif cond[ind] == 'diamond':
                    ind += 1
                    success = False
                    #TODO
                elif cond[ind] == 'line':
                    ind += 1
                    success = False
                    #TODO
                    
            if ind < len(cond) and cond[ind] == 'shield':
                ind += 1
                success = any((tile.is_shield() for tile in group))

            #DISCONNECTED CONDITIONS
            if ind < len(cond) and cond[ind] == 'opponent':
                ind += 1
                success = False
                #TODO

            if ind < len(cond) and cond[ind] == 'points':
                val = int(cond[ind+1])
                ind += 2
                success = False
                #TODO

            if ind < len(cond) and cond[ind] == 'space':
                val = int(cond[ind+1])
                ind += 2
                success = False
                #TODO

            if self.num_groups > 1:
                success = False
            

                
            
                    
##green;  1;          5;      1;         Monoculture; terrain same;
##green;  2;          3;      0;         Twin Towns; terrain same;
##blue;   1;          5;      1;         Fishing Villages; river same;
##blue;   1;          5;      1;         Hydrophobia; river none;
##blue;   1;          5;      1;         name; triangle, terrain different;
##blue;   1;          5;      1;         Diamond; diamond;
##blue;   1;          5;      1;         Linearity; line;
##blue;   1;          6;      1;         Conurbation; city 3;
##blue;   2;          1;      0;         Divided Town; points 5, space 1;
##red;    1;          5;      1;         Ambassadors; citadel share;
##red;    1;          5;      1;         Key Points; citadel, shield;
##red;    1;          5;      1;         Rival Cities; city opponent city;
##red;    1;          5;      1;         Mr Rich; city shield;
##red;    1;          5;      1;         Local Diversity; terrain 3, shield;
##red;    1;          5;      1;         Trade Route; shield, opponent;
##red;    2;          3;      0;         Friendly; opponent same;

            assert(ind == len(cond))
        return success 
                
        
class Mission_factory():
    def __init__(self):
        with open('missions.txt','r') as mission_file:
            self.fields = mission_file.readline()
            self.all_missions = [[] for i in range(NUM_MISSION_TYPES)]
            self.mission_index = [0 for i in range(NUM_MISSION_TYPES)]
            self.mission_type_lookup = {'green':0,
                                   'blue':1,
                                   'red':2}
            for mission_num, line in enumerate(mission_file.read().split('\n')):
                a_mission = Mission(line)
                self.all_missions[self.mission_type_lookup[a_mission.mission_type]].append(a_mission)
            for i in range(NUM_MISSION_TYPES):
                shuffle(self.all_missions[i])
    def __repr__(self):
        a_str = self.fields
        return a_str+'\n'.join((str(m) for mis in self.all_missions for m in mis))
    def get_mission(self,mission_type=None):        
        assert(sum(self.mission_index)<sum((len(mis) for mis in self.all_missions)))
        if mission_type != None:
            if not (self.mission_index[mission_type] < len(self.all_missions[mission_type])):
                return None
            assert(self.mission_index[mission_type] < len(self.all_missions[mission_type]))
            
        while mission_type == None:
            mission_type = randint(0,NUM_MISSION_TYPES-1)
            if self.mission_index[mission_type] >= len(self.all_missions[mission_type]):
                mission_type = None
        self.mission_index[mission_type] += 1
        return self.all_missions[mission_type][self.mission_index[mission_type]-1]
    def get_mission_types(self):
        return self.mission_type_lookup


#Each player has a set of missions and a collection of underlings, they also have resource cubes
class Player:
    def __init__(self,player_number,shop,map_grid,mission_factory):
        self.player_number = player_number
        self.map_grid = map_grid
        self.shop = shop
        self.mission_factory = mission_factory
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
        success = False
        if tile != None:
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
        success = False
        if a_mission != None:
            self.missions.append(a_mission)
            success = True
        return success
    def draw_mission(self, mission_type):
        return self.give_mission(self.mission_factory.get_mission(mission_type))
    def get_missions(self):
        return self.missions
    def get_mission_types(self):
        return self.mission_factory.get_mission_types()
    def discard_mission(self):
        selected = selectionMaker('Mission to Discard',self.missions)
        self.missions.remove(selected)
    def gain_underling(self,a_underling):
        self.underlings.append(a_underling)
    def buy_underling(self,a_underling):
        success = a_underling.do_buy(self)
        if success:
            self.gain_underling(a_underling)

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
        return not any((underling.has_action() for underling in self.underlings))
    def use_underling(self,underling_pos):
        return self.underlings[underling_pos].activate(self)
    def get_buildable(self,dist,terrain_agnostic=True,river_allowed=False,water_dist=0,citadel_only=False):
        return self.map_grid.get_buildable(self.tiles,dist,terrain_agnostic,river_allowed,water_dist,citadel_only)
    def get_buildable_sans_tile(self,tile,dist,terrain_agnostic=True,river_allowed=False,water_dist=0,citadel_only=False):
    #used to remove one tile from consideration
        return self.map_grid.get_buildable([t for t in self.tiles if t != tile],dist,terrain_agnostic,river_allowed,water_dist,citadel_only)                                
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
    def do_gain_free_underling(self):
        selected = selectionMaker('Free Underling',self.shop.all_underlings_on_sale())
        self.shop.gain(selected,self)
    def peek(self, number):
        selectionMaker('Peeked Underling',self.shop.peek(number))        
    
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
    def peek(self,number):
        age = self.check_age(self.current_round+1)
        return self.underling_factory.peek_underling(age,number)
    def check_age(self, round_number):
        age = 0
        if round_number <= 4:
            age = 1
        elif round_number <= 7:
            age = 2
        else:
            age = 3
        return age
    def all_underlings_on_sale(self):
        return [und for tier in self.shop_underlings for und in tier if und != None]
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
                    owner.buy_underling(purchase_selection)
                    purchase_selection.do_pass()
                    return True
        return False
    def gain(self,gain_selection,owner):
        if gain_selection != None:
            for shop_tier in range(NUM_SHOP_TIERS):
                for und_index in range(NUM_UNDERLINGS_SHOP_TIER):
                    if self.shop_underlings[shop_tier][und_index] == gain_selection:
                        self.shop_underlings[shop_tier][und_index] = None
                        owner.gain_underling(gain_selection)
                        gain_selection.do_pass()
                        return True
        return False   
        
class GameObject:
    def __init__(self,num_players):
        self.current_round = 0
        self.map_grid = Map_grid()
        self.mission_factory = Mission_factory()
        self.underling_factory = Underling_factory()
        self.shop = Shop(self.underling_factory)
        self.num_players = num_players
        self.players = []
        for player_num in range(self.num_players):
            self.players.append(Player(player_num,self.shop,self.map_grid,self.mission_factory))
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
                a_player.gain_underling(self.underling_factory.get_underling(0,underling).copy())
        self.start_player = randint(0,self.num_players-1)
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
        self.start_player = (self.start_player + 1)%self.num_players
        self.current_player = self.start_player
    def next_player(self, clockwise=True):
        if self.all_players_passed():
            return None
        delta = 1 if clockwise else -1 + self.num_players 
        self.current_player = (self.current_player + delta) % self.num_players 
        while self.players[self.current_player].is_passed():
            self.current_player = (self.current_player + delta) % self.num_players 
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
                show_tiles(self.map_grid,all_tiles)
                selection = selectionMaker('Player {} Initial Placement'.format(self.current_player),all_tiles)
                #selection = all_tiles[0]
                self.get_current_player().give_tile(selection)
                self.next_player(clockwise)
            self.next_player(not clockwise)
    def score_rewards(self, player, number_of_rewards):
        for n in number_of_rewards:
            if self.current_round  <= 4:
                player.give_score(6)
                players.give_resources(('s',1))
                players.give_resources(('w',1))
                players.give_resources(('g',1))
            elif self.current_round <= 7:
                player.give_score(5)
                players.give_resources(('s',1))
                players.give_resources(('w',1))
            else:
                player.give_score(4)
        
    def scoring_round(self):       
        for player_offset in range(self.num_players):
            selection_options = []
            player_num = (player_offset+self.start_player)%self.num_players
            player = self.players[player_num]
            missions = player.get_missions()
            for mission in missions:
                mission_result = self.map_grid.find_max_number_groups(player_num,mission.points,mission.check_condition)
                if mission_result != None:
                    selection_options.append((mission,mission_result))
            selection = selectionMaker('Mission to Score',['None']+selection_options)
            if selection == None:
                #TODO
                pass
        
            
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
##    go.players[0].give_tile(go.map_grid.map_tiles[2][6])
##    go.players[0].give_tile(go.map_grid.map_tiles[1][6])
##    go.players[0].give_tile(go.map_grid.map_tiles[2][7])
##    go.players[0].give_tile(go.map_grid.map_tiles[3][7])
##    go.players[0].give_tile(go.map_grid.map_tiles[4][7])
    ##    go.players[0].give_tile(go.map_grid.map_tiles[5][6])
##    go.players[0].give_tile(go.map_grid.map_tiles[4][5])
##    go.players[0].give_tile(go.map_grid.map_tiles[3][5])
##    go.players[0].give_tile(go.map_grid.map_tiles[5][7])
##    go.players[0].give_tile(go.map_grid.map_tiles[5][8])
##    go.players[0].give_tile(go.map_grid.map_tiles[5][9])
##    go.players[0].give_tile(go.map_grid.map_tiles[6][9])

    go.place_initial_settlements()
    
    for round_number in range(1,15):
        underling_name = ''
        go.new_round()
        while not go.all_players_passed():
            current_player = go.get_current_player().player_number
            if VERBOSE:
                print 'Round {}, Player {} Turn'.format(round_number, current_player)
            underling_name = selectionMaker('Underling to Activate',['Pass','Display Map','Display Shop','Display Player']+[und.name for und in go.get_current_player().underlings if und.has_action()]+['Exit'])
            success = False
            if underling_name == 'Exit':
                pass
                sys.exit(0)
            elif underling_name == 'Pass':
                success = go.get_current_player().do_pass()
                current_player = go.next_player()
            elif underling_name == 'Display Map':
                if VERBOSE:
                    print go.map_grid
            elif underling_name == 'Display Player':
                if VERBOSE:
                    print go.get_current_player()
            elif underling_name == 'Display Shop':
                if VERBOSE:
                    print go.shop
            else:
                for ind, a_underling in enumerate(go.get_current_player().underlings):
                    if a_underling.name == underling_name:
                        success = go.get_current_player().use_underling(ind)
                        break
                if success:
                    current_player = go.next_player()
                else:
                    if VERBOSE:
                        print 'action {}, failed'.format(underling_name)
        go.scoring_round()
        #mg = go.map_grid.find_max_number_groups(0,3)
        #if mg:
        #    for i,vals in enumerate(mg):
        #        print 'group {} found'.format(i),[go.map_grid.val_to_coord(val) for val in vals]
    print 'Final map'
    print go.map_grid
    

#TODO Missions, score round, selection of active underlings, choice of spending only when options exist, on_buy for underlings

    
