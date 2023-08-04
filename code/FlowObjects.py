import XMLUtils as utils
from enum import Enum
import sys

# These are the supported Flow Objects
FlowObjects = Enum('FlowObjects', 'StartEvent MessageStartEvent EndEvent Task ManualTask SendTask ReceiveTask UserTask MessageIntermediateCatchEvent IntermediateCatchEvent ParallelGateway ExclusiveGateway EventBasedGateway')

 

# Get the type of the flow object
def getFlowObjectType(flowObject):
    returnType = None
    flowObjectTagName = flowObject.tagName
    if (flowObjectTagName == "semantic:startEvent"):
        returnType = FlowObjects.StartEvent
        for child in utils.getChildren(flowObject):
            if child.tagName == "semantic:messageEventDefinition":
                returnType = FlowObjects.MessageStartEvent
    elif (flowObjectTagName == "semantic:endEvent"):
        returnType = FlowObjects.EndEvent
    elif (flowObjectTagName == "semantic:task"):
        returnType = FlowObjects.Task
    elif (flowObjectTagName == "semantic:manualTask"):
        returnType = FlowObjects.ManualTask
    elif (flowObjectTagName == "semantic:sendTask"):
        returnType = FlowObjects.SendTask
    elif (flowObjectTagName == "semantic:receiveTask"):
        returnType = FlowObjects.ReceiveTask
    elif (flowObjectTagName == "semantic:userTask"):
        returnType = FlowObjects.UserTask
    elif (flowObjectTagName == "semantic:intermediateCatchEvent"):
        returnType = FlowObjects.IntermediateCatchEvent
        for child in utils.getChildren(flowObject):
            if child.tagName == "semantic:messageEventDefinition":
                returnType = FlowObjects.MessageIntermediateCatchEvent
    elif (flowObjectTagName == "semantic:parallelGateway"):
        returnType = FlowObjects.ParallelGateway
    elif (flowObjectTagName == "semantic:exclusiveGateway"):
        returnType = FlowObjects.ExclusiveGateway
    elif (flowObjectTagName == "semantic:eventBasedGateway"):
        returnType = FlowObjects.EventBasedGateway
    else:
        sys.exit('UnsupportedFlowObject (' + flowObjectTagName + ')')
    return returnType