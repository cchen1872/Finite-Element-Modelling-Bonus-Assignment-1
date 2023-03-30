import sys

SUPPORT_TYPES = {
    "SUPPORTLESS": 0,
    "ROLLER": 1,
    "PIN": 2,
    "FIXED": 3
}

class Force:
    def __init__(self, node, x, y, z):
        self.node = node
        self.magnitudes = (x, y, z)

class Node:
    def __init__(self, x, y, z, forces, support_type):
        self.dim = (x, y, z)
        self.forces = forces
        self.support_type = support_type

class Beam:
    def __init__(self, E, end_nodes, area):
        self.E = E
        self.end_nodes = end_nodes
        self.area = area



def readNode(f):
    s = f.readline()
    force_dims = []
    support_type = SUPPORT_TYPES["SUPPORTLESS"]
    dimensions = None
    id = None
    while s != "END_NODE":
        if s == "ID:":
            id = int(f.readline())
        elif s == "DIMENSIONS:":
            dimensions = [int(x) for x in f.readline().split(',')]
        elif s == "SUPPORT_TYPE:":  
            support_type = SUPPORT_TYPES[f.readline()]
        elif s == "FORCE:":
            force_dims.append([int(x) for x in f.readline().split(',')])
        else:
            raise Exception("Invalid Node Input")
        
        s = f.readline()
    if id is None or dimensions is None:
        raise Exception("Insufficient Node Fields")
    forces = []
    for force in force_dims:
        forces.append(Force(id, *force))
    return Node(*dimensions, forces, support_type)
              

def main():
    if len(sys.argv) < 2:
        raise Exception("Did not provide input file")
    
    filename = sys.argv[1]
    f = open(filename, 'r')
    s = f.readline()
    nodes = []
    beams = []
    while s != "":
        print(s, end = '')
        s = f.readline()
        if s == "NODE:":
            nodes.append(readNode(f))
        elif s == "BEAM":
            beams.append(readBeam(f))
        else:
            raise Exception("Invalid Input")
        
    

main()