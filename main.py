import sys

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

class Beam:
    def __init__(self, id, elasticity, end_nodes, area):
        self.id = id
        self.elasticity = elasticity
        self.end_nodes = end_nodes
        self.area = area


def readBeam(f):
    s = f.readline().strip()
    elasticity = None
    area = None
    nodes = []
    id = None
    while s != "END_BEAM":
        if s == "ID:":
            id = int(f.readline().strip())
        elif s == "ELASTICITY:":
            elasticity = float(f.readline().strip())
        elif s == "AREA:":  
            area = float(f.readline().strip())
        elif s == "NODES:":
            nodes = [int(x) for x in f.readline().strip().split(',')]
        else:
            print(s)
            raise Exception("Invalid Beam Input")
        
        s = f.readline().strip()
    if len(nodes) != 2 or any([x is None for x in [elasticity, area, id]]):
        raise Exception("Insufficient Node Fields")
    return Beam(id, elasticity, nodes, area)

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

def printNode(node):
    print("NODE:")
    print(f"id: {node.id}")
    print(f"location: {node.location[0]}, {node.location[1]}, {node.location[2]}")
    for force in node.forces:
        print(f"Force: <{force.magnitudes[0]}, {force.magnitudes[1]}, {force.magnitudes[2]}>")
    print(f"Support: {SUPPORT_TYPES_KEYS[node.support_type]}\n")
def printBeam(beam):
    print("BEAM:")
    print(f"id: {beam.id}")
    print(f"nodes: {beam.end_nodes[0]} <-> {beam.end_nodes[1]}")
    print(f"elasticity: {beam.elasticity} Pa")
    print(f"area: {beam.area} m^2", end = '\n\n')
def main():
    if len(sys.argv) < 2:
        raise Exception("Did not provide input file")
    
    filename = sys.argv[1]
    f = open(filename, 'r')
    s = f.readline()
    while s == "\n":
        s = f.readline()
    s = s.strip()
    nodes = []
    beams = []
    while s != "":
        # print(s, end = '')
        if s == "\n":
            continue
        elif s == "NODE:":
            nodes.append(readNode(f))
        elif s == "BEAM:":
            beams.append(readBeam(f))
        else:
            print(s)
            print(ord(s[-1]))
            raise Exception("Invalid Input")
        s = f.readline()
        while s == "\n":
            s = f.readline()
        s = s.strip()
    for node in nodes:
        printNode(node)
    for beam in beams:
        printBeam(beam)

main()