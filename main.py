import sys
import numpy as np
from elements import Bar, Node
from elements import SUPPORT_TYPES, SUPPORT_TYPES_KEYS

ORIGIN_NODE = Node(-1, 0, 0, 0, None, None)

# Input for Bar Object
def readBar(f):
    s = f.readline().strip()
    elasticity = None
    area = None
    nodes = []
    id = None
    while s != "END_BAR":
        if s == "ID:":
            id = int(f.readline().strip())
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
    if len(nodes) != 2 or any([x is None for x in [elasticity, area, id]]):
        raise Exception("Insufficient Node Fields")
    return Bar(id, elasticity, area, nodes)

# Input for Node Object
def readNode(f):
    s = f.readline().strip()
    force_dims = None
    support_type = SUPPORT_TYPES["SUPPORTLESS"]
    dimensions = None
    id = None
    roller_direction = None
    while s != "END_NODE":
        if s == "ID:":
            id = int(f.readline().strip())
        elif s == "DIMENSIONS:":
            dimensions = [float(x) for x in f.readline().strip().split(',')]
        elif s == "SUPPORT_TYPE:":  
            support_type = SUPPORT_TYPES[f.readline().strip()]
        elif s == "FORCE:":
            force_dims = [float(x) for x in f.readline().strip().split(',')]
        elif s == "ROLLER_DIRECTION:":
            roller_direction = f.readline().strip()
        else:
            raise Exception("Invalid Node Input")
        
        s = f.readline().strip()
    if id is None or dimensions is None or \
          support_type==SUPPORT_TYPES["ROLLER"] and roller_direction is None:
        raise Exception("Insufficient Node Fields")
    
    return Node(id, *dimensions, force_dims, support_type, roller_direction)

# Looks at all bars and encapsulates the corresponding nodes into the bar objects
def connectBarNodes(bars, nodes):
    all_nodes = set()

    for node_id in nodes:
        all_nodes.add(node_id)

    for bar in bars.values():
        if bar.end_nodes is None:
            bar.end_nodes = [nodes[id] for id in bar.end_node_ids]
            for id in bar.end_node_ids:
                if id in all_nodes:
                    all_nodes.remove(id)
        else:
            for node in bar.end_nodes:
                if node.id in all_nodes:
                    all_nodes.remove(node.id)
    
    for id in all_nodes:
        del nodes[id]
    
# Uses x^2+y^2+z^2 = d^2 to find distance between two points in 3D space
def getNodeDistance(node1, node2):
    res = 0
    for coord in range(3):
        res += (node1.location[coord] - node2.location[coord]) ** 2
    res **= 0.5
    return res


# sets the bar object's cosine field
# cosines = Dx/L,Dy/L,Dz/L
def setCosines(bar):
    if bar.length is None:
        bar.length = getNodeDistance(*bar.end_nodes)
    
    bar.cosines = []
    for i in range(3):
        bar.cosines.append((bar.end_nodes[0].location[i] - bar.end_nodes[1].location[i])/bar.length)
    
# Helps signify type of boundary condition node should undergo
def findBoundaryConditions(node):
    if node.support_type >= SUPPORT_TYPES["PIN"]:
        return 0
    elif node.support_type == SUPPORT_TYPES["ROLLER"]:
        return 1
    else:
        return 2

# Applies boundary conditions to K and F
# Also removes rows/columns that are all zero in K
def trimKF(K, F, kept_rows):
    K_bc = K
    F_bc = F
    kept_rows = {kept_rows[i]:kept_rows[i] for i in range(len(kept_rows))}
    while True:
        new_K = K_bc
        new_F = F_bc
        K_bc = np.zeros((len(kept_rows), len(kept_rows)))
        F_bc = np.zeros((len(kept_rows), 1))
        idx = 0
        for row in kept_rows:
            x = np.array([new_K[row,r] for r in kept_rows])
            K_bc[idx,:] = x
            F_bc[idx,0] = new_F[row,0]
            idx += 1
        
        zeroes_h = np.zeros(len(kept_rows))
        new_kept_rows = {}
        idx = 0
        for row in kept_rows:
            if not np.array_equal(K_bc[idx,:], zeroes_h) and \
                    not np.array_equal(K_bc[:,idx], zeroes_h):
                new_kept_rows[idx] = kept_rows[row]
            idx += 1
        if len(kept_rows) == len(new_kept_rows):
            return K_bc, F_bc, sorted([elem for elem in kept_rows.values()])
        else:
            kept_rows = new_kept_rows
        
# Finds the total K before boudnary conditions by adding each
# bar's lambda matrix
def getKF(nodes, lambda_matricies):
    K = np.zeros((3*len(nodes), 3*len(nodes)))
    for node1, node2, lambda_matrix in lambda_matricies:
        starts = [3*node1, 3*node2]
        for i in range(len(starts)):
            for j in range(len(starts)):
                if i + j == 1:
                    K[starts[i]:starts[i] + 3, starts[j]:starts[j]+3] -= lambda_matrix
                else:
                    K[starts[i]:starts[i] + 3, starts[j]:starts[j]+3] += lambda_matrix
    
    F = np.zeros((3*len(nodes), 1))
    for i in range(len(nodes)):
        if nodes[i].forces is not None:
            for j in range(len(nodes[i].forces)):
                F[3*i + j,0] = nodes[i].forces[j]

    kept_rows = []
    for i in range(len(nodes)):
        bcs = findBoundaryConditions(nodes[i])
        if bcs == 1:
            roller_row = 3 * i + nodes[i].roller_move
            kept_rows.append(roller_row)     
        elif bcs >= 2:
            for j in range(len(nodes[i].location)):
                kept_rows.append(3*i + j)

    return K, F, kept_rows

# returns bar's stress given displacement and cosine vector
# sigma = E/L*[C -C]*[d1; d2] (1x6)*(6x1) = 1x1
def getStress(bar):
    n_dim = len(bar.end_nodes[0].location)
    d = np.zeros((n_dim * 2, 1))
    C = np.zeros((1, n_dim*2))
    sign = (1, -1)
    for i in range(len(bar.end_nodes)):
        d[(3*i):(3*i + n_dim)] = bar.end_nodes[i].displacement
        C[0,(3*i):(3*i + n_dim)] = sign[i] * np.array(bar.cosines)
    return bar.elasticity / bar.length * np.matmul(C, d)[0,0]
    
    

def printNode(node):
    print("NODE:")
    print(f"id: {node.id}")
    print(f"location: {node.location[0]}, {node.location[1]}, {node.location[2]}")
    print(f"Support: {SUPPORT_TYPES_KEYS[node.support_type]}")
    print(f"Displacement: \n{node.displacement}")
    print(f"Forces: {node.final_forces}\n")

def printBar(bar):
    print("Bar:")
    print(f"id: {bar.id}")
    print(f"nodes: {bar.end_nodes[0].id} <-> {bar.end_nodes[1].id}")
    print(f"stress: \n{bar.stress}\n")

def main():
    if len(sys.argv) < 2:
        raise Exception("Did not provide input file")
    
    # Read from input
    filename = sys.argv[1]
    f = open(filename, 'r')
    s = f.readline()
    while s == "\n":
        s = f.readline()
    s = s.strip()
    nodes = {}
    bars = {}
    while s != "":
        if s == "\n":
            continue
        elif s == "NODE:":
            new_node = readNode(f)
            nodes[new_node.id] = new_node
        elif s == "BAR:":
            new_bar = readBar(f)
            bars[new_bar.id] = new_bar
        else:
            raise Exception("Invalid Input")
        s = f.readline()
        while s == "\n":
            s = f.readline()
        s = s.strip()
    
    # Encapsulate node objects within bar objects
    connectBarNodes(bars, nodes)

    # converting from dictionary to list
    # Replaces ids of nodes and bars to match with index
    nodes = [node for node in nodes.values()]
    bars = [bar for bar in bars.values()]
    for i in range(len(nodes)):
        nodes[i].id = i

    for i in range(len(bars)):
        bars[i].id = i

    # Finds lambda matrix of each bar and saves within list 
    lambda_matricies = []
    for bar in bars:
        setCosines(bar)
        EAL = bar.elasticity * bar.area / bar.length
        new_lambda = EAL * np.array([[bar.cosines[i]*bar.cosines[j] \
         for j in range(len(bar.cosines))] for i in range(len(bar.cosines))])

        lambda_matricies.append((bar.end_nodes[0].id, bar.end_nodes[1].id, new_lambda))

    # Gets the K and F matricies and applies boundary conditions to them
    K, F, d_rows = getKF(nodes, lambda_matricies)
    K_bc, F_bc, d_rows = trimKF(K, F, d_rows)
    # print(K_bc, F_bc)
    d = np.linalg.solve(K_bc, F_bc)
    full_d = np.zeros((K.shape[0],1))

    # Gets full displacement matrix with boundary conditions and 
    # saves values to node objects
    d_idx = 0
    for i in range(len(nodes)):
        if d_idx >= len(d_rows):
            break
        for j in range(len(nodes[i].location)):
            if d_rows[d_idx] == 3 * i + j:
                full_d[3*i+j,0] = d[d_idx,0]
                nodes[i].displacement[j,0] = d[d_idx,0]
                d_idx += 1
                if d_idx >= len(d_rows):
                    break
    # print(full_d)

    # gets force at each node by multiplying K without boundary conditions with 
    # full displacement vector
    full_f = np.matmul(K,full_d)
    for i in range(len(nodes)):
        nodes[i].final_forces = full_f[3*i:3*i+3,0]

    # Find bar's stress
    for bar in bars: 
        bar.stress = getStress(bar)
    
    # Prints nodes and bars
    for node in nodes:
        printNode(node)
    for bar in bars:
        printBar(bar)


main()