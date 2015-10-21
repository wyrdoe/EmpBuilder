from Util import *
from itertools import combinations
class Tile:
    def __init__(self,x,y,terrain):
        self.x = x
        self.y = y
        self.terrain = terrain if terrain != '.' else None
        self.neighbours = []
        self.owner = None
        self.building_level = 0
        self.citadel = 'c'
        self.unbuilt_level = 0
        self.settlement_level = 1
        self.city_level = 2
    def __repr__(self):
        return (self.terrain if self.terrain else '.') + (str(self.owner) + str(self.building_level) if self.owner != None else '  ')
    def __str__(self):
        return '{},{}: {}'.format(self.x,self.y,(self.terrain if self.terrain else '.'))
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
        return not (self.owner!=None or self.terrain == None or self.is_citadel())
    def same_terrain(self,tile):
        return self.terrain.lower() == tile.terrain.lower() if self.terrain and tile.terrain else False
    def construct(self,player_num):
        if self.is_river_buildable():
            self.owner = player_num
            self.building_level = self.settlement_level
        else:
            return False
        return True
    def demolish(self,player_num):
        success = False
        if self.owner == player_num:
            self.owner = None
            self.building_level = self.unbuilt_level
            success = True
        return success
    def upgrade(self,player_num):
        success = False
        if self.owner == player_num:
            self.building_level = self.city_level
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
        return self.building_level == self.city_level
    def is_citadel(self):
        return self.terrain.lower() == self.citadel
    def is_outer_citadel(self):
        return self.terrain == self.citadel.upper()
    def get_owner(self):
        return self.owner
    def coords(self):
        return (self.x,self.y)
        
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
    def tile_at_val(self,val):
        x,y = self.val_to_coord(val)
        return self.map_tiles[x][y]
    #Check if a list of sets contain any overlapping items
    def sets_overlap(self,list_of_sets):
        for i,a in enumerate(list_of_sets):
            for j,b in enumerate(list_of_sets):
                if i != j:
                    if any(k in a for k in b):
                        return True
        return False
    def find_max_number_groups(self,player_num,points,cond):
        valid_combinations = self.find_groups_worth_points(player_num,points,cond)
        for num in range(1,len(valid_combinations))[::-1]:
            for comb in combinations(valid_combinations,num):
                complimentary = True
                #check no tiles are used multiple times
                if not self.sets_overlap(comb):
                    ret_val = []
                    for a_comb in comb:
                        ret_val.append([self.tile_at_val(val) for val in a_comb])
                    return ret_val
        return None
    #find all subgroups which meet the points criteria #TODO do we want to test condition here too?
    def find_groups_worth_points(self,player_num,points,cond):
        valid_combinations = []
        for group in self.connected_groups(player_num):
            #Minimum size is points / 2 since cities are worth 2 points
            for group_size in range((points+1)/2,len(group)):
                for comb in combinations(group,group_size):
                    score = 0
                    for ind, val_a in enumerate(comb):
                        tile_a = self.tile_at_val(val_a)
                        score += tile_a.building_level
                        if ind >= len(comb)-1:
                            conditions_met = score >= points
                        else:
                            conditions_met = False
                            for val_b in comb[ind+1:]:
                                if tile_a in self.tile_at_val(val_b).get_neighbours():
                                    conditions_met = True
                                    break
                        if not conditions_met:
                            break
                    if conditions_met and cond(self,[self.tile_at_val(v) for v in comb]):
                        valid_combinations.append(comb[:])
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
                        self.recurse_connections(tile,owner,lambda tile, owner: tile.get_owner() == owner, group)
                        found_groups.append([coord for coord, dist in group])
        return found_groups
    
    #find all connected settlements
    def recurse_connections(self,tile,condition_arg,condition,group_so_far,dist=None,dist_decrement=None,dist_stop_condition=None):
        if dist_decrement == None:
            dist_decrement = lambda tile, dist: dist - 1 if dist != None else None
        if dist_stop_condition == None:
            dist_stop_condition = lambda tile, dist: dist != None and dist < 0
        if not dist_stop_condition(tile,dist):
            new_dist = dist_decrement(tile,dist)
            group_so_far.add((self.coord_to_val(*tile.coords()),dist))
            for a_tile in tile.get_neighbours():
                if condition(a_tile,condition_arg) and (self.coord_to_val(*a_tile.coords()),new_dist) not in group_so_far:
                    self.recurse_connections(a_tile,condition_arg,condition,group_so_far,new_dist,dist_decrement,dist_stop_condition)
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
                        found_groups.append([coord for coord,dist in group])
        return found_groups
    def get_river_neighbours(self):
        if not hasattr(self, 'river_neighbours'):
            self.river_neighbours = []
            for a_river in self.get_rivers():
                a_river_nieghbours = set()
                for river_tile_val in a_river:
                    for a_neighbour in self.tile_at_val(river_tile_val ).get_neighbours():
                        a_river_nieghbours.add(a_neighbour)
                self.river_neighbours.append(a_river_nieghbours)
        return self.river_neighbours

    def get_buildable(self,owned_tiles, dist=None, terrain_agnostic=True, river_allowed=False, water_dist=0, citadel_only=False): #get_buildable(self.tiles,dist,terrain_agnostic,river_allowed,water_dist)
        if dist == None:
            return self.get_buildable_global(river_allowed,citadel_only)
        extra_tiles = set()
        river_buidable = set()
        if river_allowed:
            condition = lambda dest_tile, source_tile: dest_tile.is_river_buildable()
        elif not terrain_agnostic:
            condition = lambda dest_tile, source_tile: dest_tile.is_buildable() and source_tile.same_terrain(dest_tile)
        else:
            condition = lambda dest_tile, source_tile: dest_tile.is_buildable()
        search_condition = lambda dest_tile, source_tile: dest_tile.is_river_buildable()
        dist_decrement = lambda tile, dist: (dist[0], dist[1] - 1 if dist[1] != None else dist[1]) if tile.is_river() else (dist[0] - 1, 0)
        dist_stop_condition = lambda tile, dist: dist[1] != None and dist[1] <= 0 if tile.is_river() else dist[0] != None and dist[0] <= 0
        all_options = set()
        for tile in owned_tiles:
            group = set()
            for nt in tile.get_neighbours():
                self.recurse_connections(nt, tile, search_condition, group, (dist, water_dist), dist_decrement,dist_stop_condition)
            for coord,d in group:
                x,y = self.val_to_coord(coord)
                buidable_tile = self.map_tiles[x][y]
                if condition(buidable_tile,tile):
                    all_options.add(buidable_tile)
        return list(all_options)
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
