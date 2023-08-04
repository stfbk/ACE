import xml.dom.minidom
import sys
from FlowObjects import getFlowObjectType
from ConnectingObjects import getConnectingObjectType


# Get the name of the element, if present,
# otherwise, return None
def getNameOrNone(element):
    returnString = None
    if element.hasAttribute("name"):
        returnString = element.getAttribute("name").replace('\n', ' ')
    return returnString

# Get the name of the given data store, if 
# present, otherwise get the ID of the data store
def getDataStoreNameOrID(workflow, dataStoreReference):
    returnString = None
    dataStoreID = dataStoreReference.getAttribute("id") 
    dataStoreName = getNameOrNone(dataStoreReference)
    if (dataStoreName == None):
        if (dataStoreReference.hasAttribute("dataStoreRef")):
            dataStoreRefValue = dataStoreReference.getAttribute("dataStoreRef")
            dataObject = workflow.getElementById(dataStoreRefValue)
            dataStoreName = getNameOrNone(dataObject)
            if (dataStoreName != None):
                returnString = dataStoreName
            else:
                returnString = dataStoreID
        else:
            returnString = dataStoreID
    else:
        returnString = dataStoreName
    return returnString


# Get the name of the element, if present,
# otherwise get the ID of the element
def getNameOrID(element):
    returnString = None
    if element.hasAttribute("name"):
        returnString = element.getAttribute("name")
    elif element.hasAttribute("id"):
        returnString = element.getAttribute("id")
    return returnString.replace("\n", " ").replace("/", " ")


# Get the flow object type of
# the element with the given ID.
def getFlowObjectTypeFromID(workflow, elementID):
    return getFlowObjectType(workflow.getElementById(elementID))


# Get the flow object type of
# the element with the given ID.
def getConnectingObjectTypeFromID(workflow, elementID):
    return getConnectingObjectType(workflow.getElementById(elementID))


# Get the name, if present, of the element
# with the given ID, None otherwise
def getNameFromID(workflow, elementID):
    returnString = None
    element = workflow.getElementById(elementID)
    if element.hasAttribute("name"):
        returnString = element.getAttribute("name")
    return returnString


# Return the name of the element, if present.
# Otherwise, return the ID, if present. Otherwise,
# return the 'str' of the element
def getStr(currentElement):
    returnString = "'str:" + str(currentElement) + "'"
    if currentElement.hasAttribute("name"):
        returnString = "'name:" + currentElement.getAttribute("name") + "'"
    elif currentElement.hasAttribute("id"):
        returnString = "'id:" + currentElement.getAttribute("id") + "'"
    return returnString


# Often, we have attributes named "id" but they are not 
# of type "ID", i.e., those searched with the 'getElementById'
# function. Therefore, we manually set the 'id' attribute as
# the ID of each element
def setIDs(currentElement):    
    children = getChildren(currentElement)
    for child in children:
        if child.hasAttribute("id"):
            child.setIdAttribute("id")
            setIDs(child)


# Return the children of the given element 
def getChildren(element):
    return getElementNodes(element.childNodes)

# Return the ELEMENT_NODE only list of elements 
def getElementNodes(listOfElements):
    return [node for node in listOfElements if (node.nodeType == xml.dom.minidom.Node.ELEMENT_NODE)]


# Extract the name of the workflow
def getWorkflowName(workflow):
    semanticDefinitions = workflow.getElementsByTagName("semantic:definitions")[0]
    if semanticDefinitions.hasAttribute("name"):
        return semanticDefinitions.getAttribute("name")
    else:
        return None

# Check whether the given start event is the main one
# TODO check strategies for main start event
def isMainStartEvent(startEvent):
    children = getChildren(startEvent)
    lenChildren = len(children)
    if (lenChildren == 1):
        return True
    else:
        return False



# Return a list with the IDs of all start events
def getAllStartEventsID(workflow):
    startEventIDs = []
    for startEvent in workflow.getElementsByTagName("semantic:startEvent"):
        startEventIDs.append(startEvent.getAttribute("id"))

    return startEventIDs



# Get the ID of the main start event. Exit if
# there is no or there are multiple main start events
def getMainStartEventID(workflow):
    semanticStartEvents = workflow.getElementsByTagName("semantic:startEvent")
    i = 0
    idOfMainStartEvent = None
    for startEvent in semanticStartEvents:
        i = i + 1
        currentID = startEvent.getAttribute("id")
        if (isMainStartEvent(startEvent)):
            if (idOfMainStartEvent != None):
                sys.exit('TwoOrMoreMainStartEvents')
            else: 
                idOfMainStartEvent = currentID

    if (idOfMainStartEvent == None):
        sys.exit('NoMainStartEvent')

    return idOfMainStartEvent
    


# Get the ID of the pool the element 
# is in, if any. Otherwise, return None
def getPoolOfElementID(workflow, elementID):
    poolID = None

    element = workflow.getElementById(elementID)
    while element.parentNode:
        element = element.parentNode
        if (element.tagName == "semantic:process"):
            poolID = getNameOrID(element)
            break
            
    return poolID



# Get the ID of the lane the element 
# is in, if any. Otherwise, return the pool
def getLaneOfElementID(workflow, elementID):
    laneID = None

    # Check whether the element is in a lane
    lanes = workflow.getElementsByTagName("semantic:lane")
    i = 0
    for lane in lanes:
        i = i + 1
        flowNodeRefs = getChildren(lane)
        for flowNodeRef in flowNodeRefs:
            if (flowNodeRef.firstChild.nodeValue == elementID):
                laneID = getNameOrID(flowNodeRef.parentNode)

    # Otherwise, return the pool
    if (laneID == None):
        laneID = getPoolOfElementID(workflow, elementID)
            
    return laneID