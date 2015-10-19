from Util import *
from random import shuffle
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
    def peek_underling(self,underling_type,number):
        ind = self.underling_index[underling_type]-1
        if ind < len(self.all_underlings[underling_type]):
            number = min(number, len(self.all_underlings[underling_type])-ind)
            return self.all_underlings[underling_type][ind:ind+number]
        else:
            return None
    def __repr__(self):
        a_str = self.fields
        return a_str+'\n'.join((str(u) for und in self.all_underlings for u in und))
    #return an underling to the deck
    def discard(self,a_underling):
        self.all_underlings[self.underling_type_lookup[a_underling.underling_type]].append(a_underling)

class Underling():
    def __init__(self,line):
        self.line = line
        line_split = line.strip().split(';')
        self.underling_type = line_split[0].strip().lower()
        self.cost     = self.transient_resource_parse(line_split[1])
        self.on_buy   = line_split[2].strip().lower()
        self.pass_reward  = [self.transient_resource_parse(reward_str) for reward_str in line_split[3].strip().split('|')]
        self.name     = line_split[4].strip()
        self.activate_text = " ".join(line_split[5:]).lower().strip()
        self.reset()
    def copy(self):
        return Underling(self.line)
    def __repr__(self):
        return '{:6} {:4} {:4} {:4} {:20} {}'.format(self.underling_type,self.cost,self.on_buy, self.pass_reward, self.name,self.activate_text)
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
    def do_buy(self,owner):
        success = True
        for event in self.on_buy.split(','):
            acts = event.split()
            ind = 0
            if acts[ind] == '0':
                ind += 1
                pass
            elif acts[ind] == 'score':
                owner.give_score(int(acts[ind+1]))
                ind += 2
            elif acts[ind] == 'gain':
                success = self.do_act(' '.join(acts[ind:]),owner)
                ind += 2
            elif acts[ind] == 'draw':
                ind += 1
                num = int(acts[ind])
                ind += 1
                if acts[ind] == 'mission':
                    ind+=1
                    for i in range(num):
                        mission_types = owner.get_mission_types()
                        success = False
                        while not success:
                            selected = selectionMaker('Type of Mission to Draw',mission_types.keys())
                            success = owner.draw_mission(mission_types[selected])
            elif acts[ind] == 'discard':
                ind += 1
                num = int(acts[ind])
                ind += 1
                if acts[ind] == 'mission':
                    ind+=1
                    for i in range(num):
                        owner.discard_mission()
            elif acts[ind] == 'underling':
                ind += 1
                owner.do_gain_free_underling()
            elif acts[ind] == 'return':
                ind += 1
                success = False
        if ind != len(acts):
            print [self],[ind], [acts]
            assert(0)
        return success
        
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
            water_dist = 0
            citadel_only = False
            terrain_agnostic = True
            if len(act) > ind:
                if act[ind] == 'river':
                    river_allowed = True
                    water_dist = None
                    ind += 1
                elif act[ind] == 'water':
                    water_dist = int(act[ind+1])
                    ind += 2
                elif act[ind] == 'citadel':
                    citadel_only = True
                    dist = None
                    ind += 1
                elif act[ind] == 'anywhere':
                    ind += 1
                    dist = None
                    river_allowed = True
                elif act[ind] == 'cross':
                    terrain_agnostic = False
                    
            #Add basic cost tiles:
            if all((owner.check_resources(rc) for rc in resource_cost)):
                buildable_tiles = [(tile, resource_cost) for tile in owner.get_buildable(dist,terrain_agnostic,river_allowed,water_dist,citadel_only)]
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
                    buildable_tiles += [(tile, resource_cost) for tile in owner.get_buildable(dist,terrain_agnostic,river_allowed,water_dist,citadel_only)]
            #Add further cost tiles:
            
            if len(buildable_tiles) == 0:
                success = False
            else:
                if len(buildable_tiles) > 1:
                    show_tiles(owner.map_grid,[t for t, c in buildable_tiles])
                    tile,cost = selectionMaker('Settlement to Build',buildable_tiles)
                else:
                    tile,cost = buildable_tiles[0]
                success = owner.give_tile(tile)
            if success:
                assert(all((owner.take_resources(rc) for rc in cost)))
                                     
        elif act[ind] == 'gain':
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
                        show_tiles(owner.map_grid,all_settlements)
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
                ind += 1
            if success:
                owner.give_score(reward)
                                     
        elif act[ind] == 'move':
            ind += 1
            all_tiles = []
            source_tiles = [t for t in owner.get_tiles() if t != tile]
            show_tiles(owner.map_grid,source_tiles)
            source_tile = selectionMaker('Settlement to Move', ['None'] + source_tiles)
            if act[ind] == 'here':
                assert(tile != None)
                all_tiles = [t for t in tile.get_neighbours() if t.is_buildable()]
                ind += 1
            elif act[ind] == 'owned':
                all_tiles = owner.get_buildable_sans_tile(source_tile,dist=1,terrain_agnostic=True,river_allowed=False,water_dist=0)
                ind += 1
            elif act[ind] == 'anywhere':
                all_tiles = owner.get_buildable(dist=None,terrain_agnostic=True,river_allowed=True,water_dist=0,citadel_only=False)
                ind += 1
            if source_tile == 'None':
                success = False
            else:
                show_tiles(owner.map_grid,all_tiles)
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
            if all((owner.check_resources(rc) for rc in resource_cost)) and total_cost > 0:
                owner.give_score(total_cost)
                success = True
            if success:
                assert(all((owner.take_resources(rc) for rc in resource_cost)))
        elif act[ind] == 'trade':
            ind += 1
            resources = []
            for cost in act[ind].split('+'):
                resources += self.resource_parse(owner,cost,'Traded Resource',optional=True)
            resource_quantity = self.resource_combine(resources)
            total_quantity = sum((cost for resource, cost in resource_quantity))
            ind += 1
            if all((owner.check_resources(rc) for rc in resource_quantity)) and total_quantity > 0:
                success = self.do_act(act='gain {}wsg'.format(total_quantity),owner=owner,tile=None)
            if success:
                assert(all((owner.take_resources(rc) for rc in resource_quantity)))
        elif act[ind] == 'peek':
            ind += 1
            owner.peek(int(act[ind]))
            ind += 1
        elif act[ind] == 'bridge':
            #TODO later when bridge rules are final
            ind += 1
        elif act[ind] == 'beguile':
            ind += 1
            #TODO beguile: put any card from the deck into the public area. You may draw coinds and buy and underling right now.
        else:
            pass
        if ind != len(act):
            print [self],[ind],[act]
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
            elif to_parse[0] == 's': #number of shields
                condition = lambda tile: tile.is_shield()
            elif to_parse[0] == 'c': #number of citadels
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
