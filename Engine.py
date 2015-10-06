from random import shuffle, randint

class Tile:
    def __init__(self,x,y,terrain):
        self.x = x
        self.y = y
        self.terrain = terrain if terrain != '.' else None
        self.neighbours = []
        self.owner = None
    def add_neighbour(self,neighbour):
        if neighbour.terrain != None and self.terrain != None:
            self.neighbours.append(neighbour)
        else:
            return False
        return True
    def get_neighbours():
        return self.neighbours
    def construct(player_num):
        if not self.owner:
            self.owner = player_num
            self.building_level = 1
        else:
            return False
        return True
    def get_owner(self):
        return self.owner
    def upgrade(player_num):
        if self.get_owner() == player_num:
            self.building_level += 1
        else:
            return False
        return True
    def __repr__(self):
        return self.terrain if self.terrain else '.'
class Underling:
    def __init__(self):
        pass
class Map_grid:
    def __init__(self):
        with open('map.txt','r') as map_file:
            self.map_dimension = int(map_file.readline())
            self.map_tiles = [[0]*self.map_dimension for i in range(self.map_dimension)]
            for y, line in enumerate(map_file.read().split('\n')):
                for x, terrain in enumerate(line.strip().split(' ')):
                    self.map_tiles[y][x] = Tile(y, x, terrain)
                    if y % 2 == 1:
                        #all_dirs = ((0,-1), (0,1), (-1,-1), (-1,0), (1,-1), (1,0))
                        all_dirs = ((0,-1), (-1,0), (-1,-1))
                    else:
                        #all_dirs = ((0,-1), (0,1), (-1, 1), (-1,0), (1, 0), (1,1))
                        all_dirs = ((0,-1), (-1,0), (-1, 1))
                    for dir_x, dir_y in all_dirs:
                        self.add_mutual_neighbours(self.map_tiles[y][x],dir_x,dir_y)
    def add_mutual_neighbours(self, tile_a,x,y):
        if x > 0 and x < self.map_dimension and y > 0 and y < self.map_dimension:
            tile_b = self.map_tiles[x1][y1]
            assert(tile_a.add_neighbour(tile_b) == tile_b.add_neighbour(tile_a))

    def __repr__(self):
        lines = [str(self.map_dimension)]
        for y in range(self.map_dimension):
            line = [''] if y % 2 else []
            for x in range(self.map_dimension):
                line.append(str(self.map_tiles[y][x]))
            lines.append(' '.join(line))
        return '\n'.join(lines)

class Mission():
    def __init__(self, line):
        line_split = line.strip().split()
        self.mission_type   = line_split[0]
        #TODO add name
        self.num_groups     = line_split[1]
        self.points         = line_split[2]
        self.connected      = line_split[3]
        self.condition_text = " ".join(line_split[4:])
        self.conditions = []
        for cond in self.condition_text.split(','):
            self.conditions.append(self.condition_parse(cond.strip()))
    def condition_parse(self, condition_text):
        #TODO return anonymous function that checks the condition
        return None
    def __repr__(self):
        return '{:5}    {}    {}    {}    {}'.format(self.mission_type, self.num_groups, self.points, self.connected, self.condition_text)
        
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
        a_str = self.fields+'\n'
##        print all_missions
        return a_str+'\n'.join((str(m) for mis in self.all_missions for m in mis))
            
            
class Player:
    def __init__(self,player_number):
        self.player_number = player_number
        self.missions = []
        self.underlings = []       
    def __repr__(self):
        return 'player_number: {}\nMissions:\n{}\nUnderlings:\n{}'.format(self.player_number,
                                                                       '\n'.join((str(m) for m in self.missions)),
                                                                       '\n'.join(self.underlings))
    def give_mission(self,a_mission):
        self.missions.append(a_mission)
        
class GameObject:
    def __init__(self,num_players):
        self.map_grid = Map_grid()
        self.mission_factory = Mission_factory()
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
    def __repr__(self):
        return '\n'.join([str(self.map_grid),str(self.mission_factory),str(self.players)])
NUM_MISSIONS_EACH = 7
NUM_MISSION_TYPES = 3
if __name__ == "__main__":
    print GameObject(2)
