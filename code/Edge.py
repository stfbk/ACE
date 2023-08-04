from dataclasses import dataclass
from ConnectingObjects import ConnectingObjects
from FlowObjects import FlowObjects

@dataclass(unsafe_hash=True)
class Edge:
    '''Class for an edge in the graph.'''
    sourceID: str
    targetID: str
    sourceName: str
    targetName: str
    sourceType: FlowObjects
    targetType: FlowObjects
    edgeType: ConnectingObjects
    messageID: str
    loopIDs: set

    def __init__(
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
        self.loopIDs = set()
        self.sourceID = sourceID
        self.targetID = targetID
        self.sourceName = sourceName
        self.targetName = targetName
        self.sourceType = sourceType
        self.targetType = targetType
        self.edgeType = edgeType
        self.messageID = messageID

    def getSourceNameOrTypeAndID(self):
        if (self.sourceName == None):
            return str(self.sourceType) + "_" + self.sourceID
        else:
            return self.sourceName + "_" + self.sourceID

    def getTargetNameOrTypeAndID(self):
        if (self.targetName == None):
            return str(self.targetType) + "_" + self.targetID
        else:
            return self.targetName + "_" + self.targetID

    def getSourceAndTargetNameOrTypeAndID(self):
        return self.getSourceNameOrTypeAndID() + "_" + self.getTargetNameOrTypeAndID()

    def toString(self):
        belongsToLoop = ""
        if (not self.loopIDs):
            belongsToLoop = " (no loops)"
        else:
            belongsToLoop = " (loops " + str(self.loopIDs) + ")"
        return (
            "Edge " 
            + str(self.edgeType) 
            +  ": " 
            + self.getSourceNameOrTypeAndID() 
            + " => " 
            + self.getTargetNameOrTypeAndID() 
            + belongsToLoop
        )

    def markBelongToLoop(self, loopID):
        self.loopIDs.add(loopID)

    # Return a deep clone of this object
    def deepClone(self):
        clone = Edge(
            self.sourceID, 
            self.targetID, 
            self.sourceName, 
            self.targetName, 
            self.sourceType, 
            self.targetType, 
            self.edgeType,
            self.messageID
        )
        for loopID in self.loopIDs:
            clone.markBelongToLoop(loopID)
        return clone
