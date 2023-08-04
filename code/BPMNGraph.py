from BPMNVisualization import BPMNVisualization
from ConnectingObjects import ConnectingObjects
from Vertex import Vertex
from Edge import Edge
from io import UnsupportedOperation

# Defining a Class
class BPMNGraph:
   
    def __init__(self, logging):
          
        # the set of vertices (all Flow Objects) in the BPMN workflow
        self.vertices = []

        # the set of edges (all Connecting Objects) in the BPMN workflow
        self.edges = []

        # save reference to the logger object
        self.logging = logging

        # instance of class to visualize the graph
        self.G = BPMNVisualization()

    # Add a vertex to the list
    def addVertex(
        self, 
        id,
        name,
        pool,
        lane,
        vertexType,
        requiredMessages,
        producedMessages,
        requiredDataStores,
        producedDataStores,
        requiredDataObjects,
        producedDataObjects,
        partiallyExplored
    ):
        self.vertices.append(Vertex(
            id=id,
            name=name,
            pool=pool,
            lane=lane,
            vertexType=vertexType,
            requiredMessages=requiredMessages,
            producedMessages=producedMessages,
            requiredDataStores=requiredDataStores,
            producedDataStores=producedDataStores,
            requiredDataObjects=requiredDataObjects,
            producedDataObjects=producedDataObjects,
            partiallyExplored=partiallyExplored
        ))

    # Add an edge to the list
    def addEdge(
        self, 
        sourceID,
        targetID,
        sourceName,
        targetName,
        sourceType,
        targetType,
        edgeType,
        messageID
    ):
        self.edges.append(Edge(
            sourceID=sourceID, 
            targetID=targetID, 
            sourceName=sourceName, 
            targetName=targetName,
            sourceType=sourceType,
            targetType=targetType,
            edgeType=edgeType,
            messageID=messageID
        ))

    # Print number of vertices and edges
    def printInfo(self):
        self.logging.info("There are " + str(len(self.vertices)) + " vertices and " + str(len(self.edges)) + " edges")
        for edge in self.edges:
            self.logging.info(edge.getSourceNameOrTypeAndID() + " => " + edge.getTargetNameOrTypeAndID())

    # Print all vertices
    def printVertices(self):
        for vertex in self.vertices:
            self.logging.info(vertex)

    # Print all edges
    def printEdges(self):
        for edge in self.edges:
            self.logging.info(edge.getSourceNameOrTypeAndID() + " => " + edge.getTargetNameOrTypeAndID())

    # Check whether a vertex with the given ID already exists in the set of vertices
    def isThereVertexWithID(self, vertexID):
        for vertex in self.vertices:
            if (vertex.id == vertexID):
                return True
        return False

    # Build the graph
    def buildGraph(self):
        for vertex in self.vertices:
            self.G.addVertex(vertex.getNameOrTypeAndID())
        for edge in self.edges:
            if (edge.edgeType == ConnectingObjects.Sequence):
                self.G.addSequenceFlow(edge.getSourceNameOrTypeAndID(), edge.getTargetNameOrTypeAndID())    
            else:
                raise UnsupportedOperation("UnsupportedEdgeType (" + edge.edgeType + ")")

        self.G.buildGraph()

    # Print the graph
    def printGraph(self):
        self.G.visualize()

    # Return the vertices 
    def getVertices(self):
        return self.vertices

    # Return the vertex given the ID 
    def getVertexByID(self, elementID):
        return [vertex for vertex in self.vertices if (vertex.id == elementID)][0]

    # Return all edges with the given source 
    def getEdgesBySourceID(self, sourceID):
        return [edge for edge in self.edges if (edge.sourceID == sourceID)]

    # Return all edges with the given target
    def getEdgesByTargetID(self, targetID):
        return [edge for edge in self.edges if (edge.targetID == targetID)]

    # Return the loops in the graph
    def findLoops(self):
        return self.G.findLoops()

    # Mark the vertices in the given list of loops
    # and all edges connecting those vertices as
    # belonging to a loop
    def markEdgesAndVerticesInLoops(self, loops):
        loopID = 0
        # For each loop
        for loop in loops:
            loopID = loopID + 1
            for vertexInLoop in loop:
                for vertexInGraph in self.vertices:
                    if (vertexInLoop == vertexInGraph.getNameOrTypeAndID()):
                        vertexInGraph.markBelongToLoop(loopID)
            # We need to mark also edges belonging to loops
            for edgeInGraph in self.edges:
                sourceVertex = self.getVertexByID(edgeInGraph.sourceID).getNameOrTypeAndID()
                targetVertex = self.getVertexByID(edgeInGraph.targetID).getNameOrTypeAndID()
                if (sourceVertex in loop and targetVertex in loop):
                    edgeInGraph.markBelongToLoop(loopID)