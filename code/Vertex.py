from dataclasses import dataclass
import re
from FlowObjects import FlowObjects

@dataclass(unsafe_hash=True)
class Vertex:
    '''Class for a vertex in the graph.'''
    id: str
    name: str
    pool: str
    lane: str
    vertexType: FlowObjects
    requiredMessages: set
    producedMessages: set
    requiredDataStores: set
    producedDataStores: set
    requiredDataObjects: set
    producedDataObjects: set
    loopIDs: set
    partiallyExplored: bool

    def __init__(
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
        self.loopIDs = set()
        self.id = id
        self.name = name
        self.pool = pool
        self.lane = lane
        self.vertexType = vertexType
        self.requiredMessages = set()
        self.requiredMessages.update(requiredMessages)
        self.producedMessages = set()
        self.producedMessages.update(producedMessages)
        self.requiredDataStores = set()
        self.requiredDataStores.update(requiredDataStores)
        self.producedDataStores = set()
        self.producedDataStores.update(producedDataStores)
        self.requiredDataObjects = set()
        self.requiredDataObjects.update(requiredDataObjects)
        self.producedDataObjects = set()
        self.producedDataObjects.update(producedDataObjects)
        self.partiallyExplored = partiallyExplored
        


    def getNameOrTypeAndID(self):
        if (self.name == None):
            return str(self.vertexType) + "_" + self.id
        else:
            return self.name + "_" + self.id

    def markBelongToLoop(self, loopID):
        self.loopIDs.add(loopID)

    def getProducedMessages(self):
        return self.producedMessages

    def getProducedDataStores(self):
        return self.producedDataStores
    
    def getProducedDataObjects(self):
        return self.producedDataObjects
    
    def setProducedMessages(self, producedMessages):
        self.producedMessages = producedMessages
    
    def setProducedDataStores(self, producedDataStores):
        self.producedDataStores = producedDataStores
     
    def setProducedDataObjects(self, producedDataObjects):
        self.producedDataObjects = producedDataObjects
 
    def getRequiredMessages(self):
        return self.requiredMessages
      
    def getRequiredDataStores(self):
        return self.requiredDataStores
       
    def getRequiredDataObjects(self):
        return self.requiredDataObjects
   
    def getloopIDs(self):
        return self.loopIDs
 
    def setRequiredMessages(self, requiredMessages):
        self.requiredMessages = requiredMessages
 
    def setRequiredDataStores(self, requiredDataStores):
        self.requiredDataStores = requiredDataStores
   
    def setRequiredDataObjects(self, requiredDataObjects):
        self.requiredDataObjects = requiredDataObjects
  
    def getPartiallyExplored(self):
        return self.partiallyExplored
 
    def setPartiallyExplored(self, partiallyExplored):
        self.partiallyExplored = partiallyExplored

    def toString(self):
        belongsToLoop = ""
        if (not self.loopIDs):
            belongsToLoop = " (no loops)"
        else:
            belongsToLoop = " (loops " + str(self.loopIDs) + ")"
        return (
            "Vertex " 
            + str(self.vertexType) 
            +  ": " 
            + self.getNameOrTypeAndID() 
            + belongsToLoop
        )

    # Return a deep clone of this object
    def deepClone(self):
        clone = Vertex(
            self.id, 
            self.name, 
            self.pool, 
            self.lane,
            self.vertexType,
            self.requiredMessages,
            self.producedMessages,
            self.requiredDataStores,
            self.producedDataStores,
            self.requiredDataObjects,
            self.producedDataObjects,
            self.partiallyExplored
        )
        for loopID in self.loopIDs:
            clone.markBelongToLoop(loopID)
        return clone


