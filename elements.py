import numpy as np

SUPPORT_TYPES = {
    "SUPPORTLESS": 0,
    "ROLLER": 1,
    "PIN": 2,
    "FIXED": 3
}

SUPPORT_TYPES_KEYS = {
    0: "SUPPORTLESS",
    1: "ROLLER",
    2: "PIN",
    3: "FIXED"
}

ROLLER_DIRECTIONS = {
    'x': 0,
    'y': 1,
    'z': 2
}

class Node:
    def __init__(self, id, x, y, z, forces, support_type, roller_direction = None):
        self.id = id
        self.location = (x, y, z)
        self.forces = forces
        self.support_type = support_type 
        self.roller_move = None
        if self.support_type == SUPPORT_TYPES["ROLLER"]:
            self.roller_move = ROLLER_DIRECTIONS[roller_direction]

        self.displacement = np.zeros((len(self.location),1))
        self.final_forces = np.zeros((len(self.location),1))
        
class Bar:
    def __init__(self, id, elasticity, area, end_nodes):
        self.id = id
        self.elasticity = elasticity
        self.area = area
        if type(end_nodes[0]) == type(int()):
            self.end_node_ids = end_nodes
            self.end_nodes = None
        else:
            self.end_nodes_ids = None
            self.end_nodes = end_nodes
        self.length = None
        self.cosines = None
        self.stress = None