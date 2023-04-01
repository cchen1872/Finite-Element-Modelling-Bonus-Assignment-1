import sys
from solve import solve

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

class Force:
    def __init__(self, node, x, y, z):
        self.node = node
        self.magnitudes = (x, y, z)

class Node:
    def __init__(self, id, x, y, z, forces, support_type):
        self.id = id
        self.location = (x, y, z)
        self.forces = forces
        self.support_type = support_type

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




def readBar(f):
    s = f.readline().strip()
    elasticity = None
    area = None
    nodes = []
    id = None
    while s != "END_BAR":
        print(s, s == "END_BAR")
        if s == "ID:":
            id = int(f.readline().strip())
            print(id)
        elif s == "ELASTICITY:":
            elasticity = float(f.readline().strip())
        elif s == "AREA:":  
            area = float(f.readline().strip())
        elif s == "NODES:":
            nodes = [int(x) for x in f.readline().strip().split(',')]
        else:
            print(s, id, elasticity, area, nodes)
            raise Exception("Invalid Bar Input")
        
        s = f.readline().strip()
    print("DONE")
    if len(nodes) != 2 or any([x is None for x in [elasticity, area, id]]):
        raise Exception("Insufficient Node Fields")
    return Bar(id, elasticity, area, nodes)

def readNode(f):
    s = f.readline().strip()
    force_dims = []
    support_type = SUPPORT_TYPES["SUPPORTLESS"]
    dimensions = None
    id = None
    while s != "END_NODE":
        if s == "ID:":
            id = int(f.readline().strip())
        elif s == "DIMENSIONS:":
            dimensions = [float(x) for x in f.readline().strip().split(',')]
        elif s == "SUPPORT_TYPE:":  
            support_type = SUPPORT_TYPES[f.readline().strip()]
        elif s == "FORCE:":
            force_dims.append([float(x) for x in f.readline().strip().split(',')])
        else:
            raise Exception("Invalid Node Input")
        
        s = f.readline().strip()
    if id is None or dimensions is None:
        raise Exception("Insufficient Node Fields")
    forces = []
    for force in force_dims:
        forces.append(Force(id, *force))
    return Node(id, *dimensions, forces, support_type)

def connectBarNodes(bars, nodes):
    for bar in bars.values():
        if bar.end_nodes is None:
            bar.end_nodes = [nodes[id] for id in bar.end_node_ids]
    
def saveBarLength(bar):
    res = 0
    for coord in range(3):
        res += (bar.end_nodes[0].location[coord] - bar.end_nodes[1].location[coord]) ** 2
    res **= 0.5
    bar.length = res
    return res

def saveCosines(bar):
    if bar.length is None:
        saveBarLength(bar)
    
    bar.cosines = []
    for i in range(3):
        bar.cosines.append((bar.end_nodes[0].location[i] - bar.end_nodes[1].location[i])/bar.length)
    # print(bar.cosines, bar.id)

def printNode(node):
    print("NODE:")
    print(f"id: {node.id}")
    print(f"location: {node.location[0]}, {node.location[1]}, {node.location[2]}")
    for force in node.forces:
        print(f"Force: <{force.magnitudes[0]}, {force.magnitudes[1]}, {force.magnitudes[2]}>")
    print(f"Support: {SUPPORT_TYPES_KEYS[node.support_type]}\n")
def printBar(bar):
    print("Bar:")
    print(f"id: {bar.id}")
    print(f"nodes: {bar.end_nodes[0].id} <-> {bar.end_nodes[1].id}")
    print(f"elasticity: {bar.elasticity} Pa")
    print(f"area: {bar.area} m^2")
    print(f"length: {bar.length} m")
    print(f"cosines: {bar.cosines}")

def main():
    if len(sys.argv) < 2:
        raise Exception("Did not provide input file")
    
    filename = sys.argv[1]
    f = open(filename, 'r')
    s = f.readline()
    while s == "\n":
        s = f.readline()
    s = s.strip()
    nodes = {}
    bars = {}
    while s != "":
        # print(s, end = 'KLSFJKSDLFJSKL\n')
        if s == "\n":
            continue
        elif s == "NODE:":
            new_node = readNode(f)
            nodes[new_node.id] = new_node
        elif s == "BAR:":
            new_bar = readBar(f)
            bars[new_bar.id] = new_bar
        else:
            print(s)
            print(ord(s[-1]))
            raise Exception("Invalid Input")
        s = f.readline()
        while s == "\n":
            s = f.readline()
        s = s.strip()
    connectBarNodes(bars, nodes)
    for bar in bars.values():
        saveCosines(bar)
    for node in nodes.values():
        printNode(node)
    for bar in bars.values():
        print(bar)
        printBar(bar)

    solve(nodes, bars)

main()