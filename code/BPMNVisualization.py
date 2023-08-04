# plot graph
import networkx as nx
import matplotlib.pyplot as plt

# Defining a Class
class BPMNVisualization:
   
    def __init__(self):
          
        # the set of edges representing Sequence Flow objects
        self.sequenceFlows = []

        # the set of vertices
        self.vertices = []

        # the graph
        self.G = None


    # Appends a vertex to the list
    def addVertex(self, a):   
        self.vertices.append(a)

    # Appends a sequence flow object to the list
    def addSequenceFlow(self, a, b):
        temp = [a, b]
        self.sequenceFlows.append(temp)
                     
    # Build the graph with the currently added edges
    def buildGraph(self):
        self.G = nx.DiGraph()
        self.G.add_nodes_from(self.vertices)
        self.G.add_edges_from(self.sequenceFlows, color='b', weight=1)


    # Creates a graph with the given lists of edges
    # nx.draw_networkx(G) - plots the graph
    # plt.show() - displays the graph
    def visualize(self):
        edges = self.G.edges()
        edge_colors = [self.G[u][v]['color'] for u,v in edges]
        weights = [self.G[u][v]['weight'] for u,v in edges]

        nx.draw_networkx(self.G, arrows=True, edge_color=edge_colors, width=weights, arrowsize=20)
        plt.show()

    # Return the loops in the graph
    def findLoops(self):
        return list(nx.simple_cycles(self.G))