
# Import PuLP modeler functions
from pulp import *
import pandas as pd


network1 = pd.read_excel("Locations and transit times.xlsx",sheet_name='Sheet5',encoding = "ISO-8859-1");
# Data Section
# Geographic Locations
Terminals = ['SAC', 'MRL', 'MDW', 'DAL', 'NHS']

# Time Periods (Assumes Uniform Discretization)
TimeStamps = [1, 2, 3, 4, 5, 6, 7]
# Dictionary of node net supply dictionaries
# Blank values indicate transshipment nodes
# Dictionary pairs are timestamp1: bvalue1
b = {'SAC': {1: 30, 2: -5, 3: 5, 4: 18, 5: 10, 6: 4, 7: -4},
'MRL': {1: 70, 2: -35, 3: 13, 4: 42, 5: -38, 6: -64, 7: -45},
'MDW': {1: 63, 2: -46, 3: 0, 4: 11, 5: -12, 6: -33, 7: -24},
'DAL': {1: 22, 2: -9, 3: 2, 4: 10, 5: -1, 6: -17, 7: -7},
'NHS': {1: 33, 2: -32, 3: 0, 4: 25, 5: 13, 6: 14, 7: -10}
}

Transportopt_available = network1[['Org','Timestamp_O','Dest','Timestamp_D','Transit days','Cost']].values.tolist()
TransportOptions = [(o,t1,d,t2,t,c) for (o,t1,d,t2,t,c) in Transportopt_available]

# Transportation options are used to generate time-space arcs
# for every period in TimeStamps
# (From, To, TravelTime)
"""
TransportOptions = (('A', 'D', 1),
('A', 'E', 3),
('B', 'D', 1),
('D', 'C', 3),
('E', 'F', 1),
('E', 'A', 3),
('F', 'E', 1),
('A',7,3),
('C',7,3),
('C',7,2),
('D',7,1),
)
"""

# Network Building
# In this formulation, we assume that a time-space node exists for each geographic location, at each point in time.
# Arcs are generated between time-space nodes, which are referenced using a duple (Terminal,TimeStamp)

# In this model, we build no time-space arcs that extend beyond the final
# time period in the planning horizon
#Transportation Arcs
Arcs=[]
Leadtime=[]
Cost=[]
Caps = []
for (o,t1,d,t2,tt,c) in TransportOptions:
    oNode = (o, t1)
    dNode = (d, t2)
    Arcs.append((oNode, dNode))
    Cost.append(c)
#print("The transportation arcs are: ",Arcs)
# Add inventory arcs
# Such arcs start at the first time in TimeStamps,
# and terminate into the last time in TimeStamps
indTime1 = range(len(TimeStamps) - 1)
for i in Terminals:
    for it in indTime1:
        oNode = (i, TimeStamps[it])
        dNode = (i, TimeStamps[it + 1])
        Arcs.append((oNode, dNode))
        Cost.append(0)
#print("The inventory arcs are: ",Arcs)
# We now add the source and sink arcs
for i in Terminals:
# Source arcs - (0, 0) denotes source
    #Arcs.append(((0, 0), (i, 1)))
    #Cost.append(0)
    #Caps.append(100)
# Sink arcs - (7, 6) denotes sink
    Arcs.append(((i, 7), (6, 7)))
    Cost.append(0)
# List of arc indices
indArcs = range(len(Arcs))
print(indArcs)

indArcs3 = len(Arcs)
print(indArcs3)
# Create the 'prob' object to contain the problem data
prob = LpProblem("MinCost Time Space Network Flow", LpMinimize)
# Decision variables
# Build arc flow variables for each arc, lower bounds = 0

arc_flow = []
for a in indArcs:
# Format for LpVariable("Name",Lowerbound)
# Remember that Arcs[a][0] is the tail node duple,
# and Arcs[a][1] is the head node duple
    var = LpVariable(
        "ArcFlow_(%s,%s)_(%s,%s)" % (str(Arcs[a][0][0]), str(Arcs[a][0][1]),
                  str(Arcs[a][1][0]), str(Arcs[a][1][1])), 0)
    arc_flow.append(var)
    
    
# The objective function is added to 'prob' first
prob += lpSum([Cost[a] * arc_flow[a] for a in indArcs]), "Total Cost"
# Generate a flow balance constraint for each node
for i in Terminals:
    for t in TimeStamps:
        outArcs = []
        inArcs = []
# The inefficient approach to building the lists of outbound and inbound arcs
        for a in indArcs:
            if (Arcs[a][0][0] == i) and (Arcs[a][0][1] == t):
                outArcs.append(a)
            elif (Arcs[a][1][0] == i) and (Arcs[a][1][1] == t):
                inArcs.append(a)
# The default is NetSupply = 0, and change it if found in the data
        NetSupply = 0
        if i in b:
            if t in b[i]:
                NetSupply = b[i][t]
                
            prob += lpSum([arc_flow[a] for a in outArcs]) - lpSum(
                    [arc_flow[a] for a in inArcs]) == NetSupply, "Node (%s,%s) Balance" % (str(i), str(t))
"""
print("Hello")
V=215
startArcs=[]
for a in indArcs[indArcs3:(indArcs3+4)]:
    startArcs.append(a)
#prob+= lpSum([arc_flow[a] for a in startArcs]) <= V
for a in indArcs[indArcs3:(indArcs3+4)]:
    print("Hi")
    print(v.name)
    prob += arc_flow[a] <= Caps[a]
"""
# Write out as a .LP file
prob.writeLP("TSMinCostFlow.lp")
# The problem is solved using PuLP's choice of Solver
prob.solve(GUROBI())
# The status of the solution is printed to the screen
print ("Status:", LpStatus[prob.status])
# Each of the variables is printed with it's resolved optimum value
for v in prob.variables():
    if(v.varValue != 0):
        print (v.name, "=", v.varValue)
    
# The optimised objective function value is printed to the screen
print ("Total Cost = ", value(prob.objective))

