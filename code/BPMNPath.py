import sys

class BPMNPath:
   
    def __init__(self, logging, id, group):

        # Identifier for this path
        self.id = id

        # Identifier for this group (a group of vertices
        # share the set of vertices and edges but not the
        # order in which vertices are explored)
        self.group = group

        # save reference to the logger object
        self.logging = logging

        # the set of vertices to explore
        self.verticesToExplore = []

        # the set of edges explored
        self.edgesExplored = []

        # the set of vertices explored
        self.verticesExplored = []

        # the set of IDs of messages produced
        self.messagesProduced = []

        # the set of IDs of data stores produced
        self.dataStoresProduced = []

        # the set of IDs of data stores produced
        self.dataObjectsProduced = []

    # Get hash
    def __hash__(self):
        return (hash(self.id)
            + hash(self.group)
            + hash(tuple(self.verticesToExplore)) 
            + hash(tuple(self.edgesExplored)) 
            + hash(tuple(self.verticesExplored)) 
            + hash(tuple(self.messagesProduced))
            + hash(tuple(self.dataStoresProduced))
            + hash(tuple(self.dataObjectsProduced)))

    # Check equality
    def __eq__(self, other):
        if isinstance(other, BPMNPath):
            if (self.id != other.id):
                return False
            elif (self.group != other.group):
                return False
            elif (self.verticesToExplore != other.verticesToExplore):
                return False
            elif (self.edgesExplored != other.edgesExplored):
                return False
            elif (self.verticesExplored != other.verticesExplored):
                return False
            elif (self.messagesProduced != other.messagesProduced):
                return False
            elif (self.dataStoresProduced != other.dataStoresProduced):
                return False
            elif (self.dataObjectsProduced != other.dataObjectsProduced):
                return False
            else:
                return True
        else:
            return False


    # Set the list of vertices to explore
    def setVerticesToExplore(self, verticesToExplore):
        self.verticesToExplore = verticesToExplore

    # Return the list of vertices to explore
    def getVerticesToExplore(self):
        return self.verticesToExplore

    # Add a vertex to the set of vertices to explore
    # only if we have not explored this vertex yet
    # and the vertex is not already in the set to explore
    def addVertexToExplore(self, vertex):
        vertexAlreadyToExplore = False
        vertexAlreadyExplored = False

        if (not vertex.partiallyExplored):
            for vertexToExplore in self.verticesToExplore:
                if (not vertexToExplore.partiallyExplored and vertex.id == vertexToExplore.id):
                    vertexAlreadyToExplore = True
            if (vertexAlreadyToExplore):
                self.logging.info("Path " 
                    + self.getGroupAndID() 
                    + ": vertex '" + vertex.getNameOrTypeAndID() + "' already to explore "
                    + "(it belongs to the following loops: " + str(vertex.loopIDs) + ")"
                )

            for vertexExplored in self.verticesExplored:
                if (not vertexExplored.partiallyExplored and vertex.id == vertexExplored.id):
                    vertexAlreadyExplored = True
            if (vertexAlreadyExplored):
                self.logging.info("Path " 
                    + self.getGroupAndID() 
                    + ": vertex '" + vertex.getNameOrTypeAndID() + "' already explored "
                    + "(it belongs to the following loops: " + str(vertex.loopIDs) + ")"
                )
        
        if (not vertexAlreadyToExplore and not vertexAlreadyExplored):
            self.verticesToExplore.append(vertex)

    # Pop (i.e., remove and return) the first
    # vertex in the list of vertices to explore
    def popVertexToExplore(self):
        nextVertex = self.verticesToExplore[0]        
        self.verticesToExplore.pop(0)
        return nextVertex

    # Add an edge to the set of edges explored.
    def addEdgeExplored(self, edge):
        edgeAlreadyExplored = False
        for edgeExplored in self.edgesExplored:
            if (edge.getSourceAndTargetNameOrTypeAndID() == edgeExplored.getSourceAndTargetNameOrTypeAndID()):
                edgeAlreadyExplored = True

        if (edgeAlreadyExplored):
            self.logging.info("Path " 
                + self.getGroupAndID() 
                + ": edge '" + edge.getSourceAndTargetNameOrTypeAndID() + "' already explored "
                + "(it belongs to the following loops: " + str(edge.loopIDs) + ")"    
            )
        else:
            self.edgesExplored.append(edge)


    # Add a message to the set of messages produced
    def addMessageProduced(self, message):
        if (message not in self.messagesProduced):
            self.logging.debug("Path " 
                + self.getGroupAndID() 
                + ": producing message '"
                + str(message)
                + "'"
            )
            self.messagesProduced.append(message)
        else:
            self.logging.debug("Path " 
                + self.getGroupAndID() 
                + ": received already present message to produce '"
                + str(message)
                + "'"
            )


    # Add a data store to the set of data stores produced
    def addDataStoreProduced(self, dataStore):
        if (dataStore not in self.dataStoresProduced):
            self.logging.debug("Path " 
                + self.getGroupAndID() 
                + ": producing data store '"
                + str(dataStore)
                + "'"
            )
            self.dataStoresProduced.append(dataStore)
        else:
            self.logging.debug("Path " 
                + self.getGroupAndID() 
                + ": received already present data store to produce '"
                + str(dataStore)
                + "'"
            )

    # Add a data object to the set of data objects produced
    def addDataObjectProduced(self, dataObject):
        if (dataObject not in self.dataObjectsProduced):
            self.logging.debug("Path " 
                + self.getGroupAndID() 
                + ": producing data object '"
                + str(dataObject)
                + "'"
            )
            self.dataObjectsProduced.append(dataObject)
        else:
            self.logging.debug("Path " 
                + self.getGroupAndID() 
                + ": received already present data object to produce '"
                + str(dataObject)
                + "'"
            )

    # Add a vertex to the set of vertices explored
    def addVertexExplored(self, vertex):
        vertexAlreadyExplored = False

        if (not vertex.partiallyExplored):
            for vertexExplored in self.verticesExplored:
                if (not vertexExplored.partiallyExplored and vertex.id == vertexExplored.id):
                    vertexAlreadyExplored = True
            if (vertexAlreadyExplored):
                self.logging.info("Path " 
                    + self.getGroupAndID() 
                    + ": vertex '" + vertex.getNameOrTypeAndID() + "' already explored "
                    + "(it belongs to the following loops: " + str(vertex.loopIDs) + ")"
                )

        if (not vertexAlreadyExplored):
            self.verticesExplored.append(vertex)
            for producedMessageID in vertex.getProducedMessages():
                self.addMessageProduced(producedMessageID)
            for producedDataStoreID in vertex.getProducedDataStores():
                self.addDataStoreProduced(producedDataStoreID)
            for producedDataObjectID in vertex.getProducedDataObjects():
                self.addDataObjectProduced(producedDataObjectID)
        

    # Return true if the set of vertices to explore is empty
    def isFinished(self):
        return (not self.verticesToExplore)

    # Set the identifier for this path
    def setID(self, newID):
        self.id = newID

    # Set the group for this path
    def setGroup(self, newGroup):
        self.group = newGroup

    # Return the identifier for this path
    def getID(self):
        return str(self.id)

    # Return the group for this path
    def getGroup(self):
        return str(self.group)

    # Return the group and the identifier for this path
    def getGroupAndID(self):
        return str(self.group) + "." + str(self.id)

    # Print the set of edges explored in the log
    def printToLogEdges(self):
        for edge in self.edgesExplored:
            self.logging.info(edge.toString())

    # Print the set of vertices explored in the log
    def printToLogVertices(self):
        for vertex in self.verticesExplored:
            self.logging.debug(vertex.toString())

    # Return the list of vertices explored
    def getVerticesExplored(self):
        if (self.isFinished()):
            return self.verticesExplored
        else:
            self.logging.error("Path " 
                + self.getGroupAndID() 
                + ": cannot invoke 'getVerticesExplored' if the visit is not finished"
            )
            sys.exit(1)

    # Return the explored vertix whose ID matches the given one 
    def getVertexExploredByID(self, id):
        for vertex in self.verticesExplored:
            if (vertex.id == id):
                return vertex
        return None

    # Return the list of edges explored
    def getEdgesExplored(self):
        if (self.isFinished()):
            return self.edgesExplored
        else:
            self.logging.error("Path " 
                + self.getGroupAndID() 
                + ": cannot invoke 'getEdgesExplored' if the visit is not finished"
            )
            sys.exit(1)

    # Return the ID of all messages produced
    def getMessagesProduced(self):
        return self.messagesProduced

    # Return the ID of all data stores produced
    def getDataStoresProduced(self):
        return self.dataStoresProduced

    # Return the ID of all data stores produced
    def getDataObjectsProduced(self):
        return self.dataObjectsProduced

    # Return a deep clone of this object
    def deepClone(self):
        clone = BPMNPath(self.logging, self.id, self.group)
        clonedVertexToExplore = []
        clonedVertexExplored = []
        clonedEdgeExplored = []
        clonedMessageProduced = []
        clonedDataStoreProduced = []
        clonedDataObjectProduced = []

        for vertexToExplore in self.verticesToExplore:
            clonedVertexToExplore.append(vertexToExplore.deepClone())
        for vertexExplored in self.verticesExplored:
            clonedVertexExplored.append(vertexExplored.deepClone())
        for edgeExplored in self.edgesExplored:
            clonedEdgeExplored.append(edgeExplored.deepClone())
        for messageProduced in self.messagesProduced:
            clonedMessageProduced.append(messageProduced)
        for dataStoreProduced in self.dataStoresProduced:
            clonedDataStoreProduced.append(dataStoreProduced)
        for dataObjectProduced in self.dataObjectsProduced:
            clonedDataObjectProduced.append(dataObjectProduced)

        clone.verticesToExplore = clonedVertexToExplore
        clone.verticesExplored = clonedVertexExplored
        clone.edgesExplored = clonedEdgeExplored
        clone.messagesProduced = clonedMessageProduced
        clone.dataStoresProduced = clonedDataStoreProduced
        clone.dataObjectsProduced = clonedDataObjectProduced

        return clone
