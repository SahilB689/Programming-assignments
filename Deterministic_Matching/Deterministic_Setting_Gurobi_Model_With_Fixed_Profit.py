import gurobipy as gp
from gurobipy import GRB
import numpy as np
from scipy.spatial import distance
import matplotlib.pyplot as plt 
import networkx as nx

def generate_inst(numdrivers, numorders): 
    loc_set = [[0.5 + x, 0.5 + y] for x in range(10) for y in range(10)]
    
    def closest_node(node):
        nodes = np.asarray(loc_set)
        closest_ind = distance.cdist([node], nodes).argmin() 
        return loc_set[closest_ind]

    driverlocation = [closest_node([np.random.uniform(0, 10), np.random.uniform(0, 10)]) for i in range(numdrivers)] 
 
    orderlocation = [None]
    orderrevenue = [None]
    minrevenue = 1; maxrevenue = 11 
    minrevenue = 11; maxrevenue = 21  
    
    for i in range(numorders):
        o_discrete = closest_node([np.random.uniform(0, 10), np.random.uniform(0, 10)])
        d_discrete = closest_node([np.random.uniform(0, 10), np.random.uniform(0, 10)])

        while o_discrete == d_discrete:  # to make sure origin != dest
            d_discrete = closest_node([np.random.uniform(0, 10), np.random.uniform(0, 10)])

        orderlocation.append([o_discrete, d_discrete]) 
        orderrevenue.append(np.random.randint(minrevenue, maxrevenue+1)) #random integer x where minrevenue<=x<=maxrevenue 
        
    return driverlocation, orderlocation, orderrevenue    

def dist(vec1, vec2):
    #Euclidean distance between vec1 and vec2 
    return ((vec1[0]-vec2[0])**2 + (vec1[1]-vec2[1])**2)**0.5 

def c(a, b):  
    #cost for driver a to deliver order b; proportional to Euclidean distance from driver to order origin plus Euclidean distance from order origin to order destination  
    #a is an index and not an attribute vector, as is b
    return dist([driverlocation[a][0], driverlocation[a][1]], [orderlocation[b][0][0], orderlocation[b][0][1]]) + dist([orderlocation[b][1][0], orderlocation[b][1][1]], [orderlocation[b][0][0], orderlocation[b][0][1]])

if __name__ == '__main__':
 
    numdrivers = 10; numorders = 10  
    driverlocation, orderlocation, orderrevenue = generate_inst(numdrivers, numorders)
    numorders+=1 #numorders is 1 more than actual number of orders because first element of orderlocation is None  
     
    print('driverlocation: ', driverlocation); print('orderlocation: ', orderlocation); print('orderrevenue: ', orderrevenue)
    
    m = gp.Model('driverallocation')

    assign = m.addVars([(i,j) for i in range(numdrivers) for j in range(numorders)], name = 'assign', vtype = GRB.BINARY) 
    #assign[i,j] means driver i (0-based index) is assigned to order j (1-based index; if j = 0 it indicates not being assigned to an order)

    m.addConstrs(gp.quicksum(assign[i,j] for j in range(numorders)) == 1 for i in range(numdrivers))  
    #each driver is assigned at most once (since a is an index not a vector Ra = 1) or not assigned at all 
    #constraint (4b); since each driver has a unique index, Rta is 1 

    m.addConstrs(gp.quicksum(assign[i,j] for i in range(numdrivers)) <= 1 for j in range(1, numorders)) 
    #each order (except None, which represents not being assigned) is fulfilled at most once 
    #constraint (4c); here j ranges from 1 to numorders because the possibility of unassigned orders is not relevant 

    m.setObjective(gp.quicksum((orderrevenue[j] - c(i, j))*assign[i,j] for i in range(numdrivers) for j in range(1, numorders)), GRB.MAXIMIZE)  
    #j ranges from 1 to numorders because if j = 0 no revenue is earned as a driver was not assigned     
        
    m.optimize()  
    
    #NETWORK DIAGRAM 
    
    # Initialize graph
    B = nx.Graph()
 
    top_nodes = ['Driver ' + str(i) for i in range(len(driverlocation))][::-1]
    bottom_nodes = ['Order ' + str(i) for i in range(len(orderlocation))][::-1]
    B.add_nodes_from(top_nodes, bipartite=0)
    B.add_nodes_from(bottom_nodes, bipartite=1)

    # Add edges between drivers and matched orders
    edges = [('Driver ' + str(i), 'Order ' + str(j)) for i in range(numdrivers) for j in range(numorders) if assign[i, j].x == 1]
    B.add_edges_from(edges)

    plt.figure(figsize=(10, 6))  # Adjust the figure size for better readability 

    edges = B.edges()

    pos = dict()
    pos.update((n, (1, i * 2)) for i, n in enumerate(top_nodes))  #i * 2 to Increase the spacing between nodes in X-axis
    pos.update((n, (2, i * 2)) for i, n in enumerate(bottom_nodes))  # Increase the spacing between nodes in X-axis

    nx.draw_networkx(B, pos=pos, node_size=200, node_color='skyblue', edge_color='gray')  # Customize the node and edge appearance

    plt.axis('off')  # Remove the axis

    plt.show()
