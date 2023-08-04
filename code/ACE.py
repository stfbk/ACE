#!/usr/bin/python

from io import UnsupportedOperation
from lib2to3.pgen2.tokenize import StopTokenizing

from charset_normalizer import CharsetNormalizerMatch
from XMLUtils import *
from FlowObjects import FlowObjects
from ConnectingObjects import ConnectingObjects
from BPMNGraph import BPMNGraph
from BPMNPath import BPMNPath
from xml.dom.minidom import parse
import sys, logging, argparse, time, re




# The steps are:
# 1. parse the command line arguments and the XML file containing the BPMN workflow; 
# 2. extract from the BPMN workflow all (supported) Flow Objects and Connecting Objects;
# 3. compute all possible paths (i.e., visit orders of Flow Objects) satisfying the workflow;
# 4. translate each path into a list of AC operations and write the obtained lists into a JSON file.




















# ===== ===== ===== ===== ===== ===== start 1 ===== ===== ===== ===== ===== ===== 
# Parse the command line arguments and the XML file containing the BPMN workflow
parser = argparse.ArgumentParser(description='ACE (AC state-change rule extraction procedurE)')

parser.add_argument(
    "xml", 
    type=str, 
    help="The path to the .xml file containing the BPMN workflow to parse"
)

parser.add_argument(
    "output", 
    type=str, 
    help="The path (directory) in which to save the .json file that will be produced as output"
)

parser.add_argument(
    "--logLevel", 
    type=str,
    help="Log level among 'DEBUG', 'INFO', 'WARNING' (default), 'ERROR' and 'CRITICAL'"
)

parser.add_argument(
    "--logFile", 
    type=str,
    help="File (path) where to log (default log to console)"
)

parser.add_argument(
    "--adminName", 
    type=str,
    help="In case one or more resources are expected to already exist before executing the workflow (i.e., they are not created by any activity but are assumed to be provided as an external input), we treat them as if the administrator was creating such resources. For this reason, please provide the username of the administrator (default is 'admin')"
)

parser.add_argument(
    '--allExecutions', 
    action='store_true',
    help='Compute all possible executions satisfying the workflow'
)

args = parser.parse_args()

logLevel = "WARNING" if not args.logLevel else args.logLevel
numeric_level = getattr(logging, logLevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % logLevel)

if not args.logFile:
    logging.basicConfig(level=numeric_level)
else:
    logging.basicConfig(
        filename=args.logFile,
        filemode='w',
        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
        datefmt='%H:%M:%S',
        level=numeric_level
    )

workflowXML = args.xml
outputJSON = args.output
computeAllExecutions = args.allExecutions
adminName = "admin" if not args.adminName else args.adminName

logging.info(
    """                  
  ___  _____  _____ 
 / _ \/  __ \|  ___|
/ /_\ \ /  \/| |__  
|  _  | |    |  __| 
| | | | \__/\| |___ 
\_| |_/\____/\____/ 
    """
)

# Parse the XML and setup the analysis
logging.info("Open the XML document " + workflowXML + " using minidom parser")
workflow = parse(workflowXML)

# Log general info
workflowName = getWorkflowName(workflow)
if (workflowName == None):
    workflowName = workflowXML
logging.info("Parsing the workflow '" + workflowName + "'")

logging.info("Mark the 'id' attributes as IDs for all elements")
setIDs(workflow)
# ===== ===== ===== ===== ===== ===== end 1 ===== ===== ===== ===== ===== ===== 




















# ===== ===== ===== ===== ===== ===== start 2 ===== ===== ===== ===== ===== ===== 
# Extract from the BPMN workflow all (supported) Flow Objects and Connecting Objects
logging.info("===== ===== ===== ===== ===== ===== start 2 ===== ===== ===== ===== ===== =====")
graph = BPMNGraph(logging)

edgeTags = [
    "semantic:sequenceFlow"
]
for tag in edgeTags:
    for connectingObject in workflow.getElementsByTagName(tag):
        sourceRef = connectingObject.getAttribute("sourceRef") 
        targetRef = connectingObject.getAttribute("targetRef") 
        logging.info("Adding Connecting Object " 
            + getStr(connectingObject) 
            + " from " 
            + sourceRef 
            + " to " 
            + targetRef 
            + " to the set of edges"
        )
        edgeType = ConnectingObjects.Sequence

        graph.addEdge(
            sourceID=sourceRef,
            targetID=targetRef,
            sourceName=getNameFromID(workflow, sourceRef),
            targetName=getNameFromID(workflow, targetRef),
            sourceType=getFlowObjectTypeFromID(workflow, sourceRef),
            targetType=getFlowObjectTypeFromID(workflow, targetRef),
            edgeType=edgeType,
            messageID=None
        )


vertexTags = [
    "semantic:task", 
    "semantic:manualTask",
    "semantic:sendTask",                
    "semantic:receiveTask",                
    "semantic:userTask",                
    "semantic:startEvent", 
    "semantic:endEvent", 
    "semantic:intermediateCatchEvent", 
    "semantic:parallelGateway",
    "semantic:exclusiveGateway", 
    "semantic:eventBasedGateway"
]
for tag in vertexTags:
    for flowObject in workflow.getElementsByTagName(tag):
        flowObjectID = flowObject.getAttribute("id") 
        flowObjectName = getNameOrNone(flowObject) 
        logging.info("Adding Flow Object " 
            + getStr(flowObject) 
            + " of type "
            + str(getFlowObjectType(flowObject))
            + " to the set of vertices"
        )

        # Collect the IDs of messages required by this vertex
        requiredMessages = set()
        for messageFlow in workflow.getElementsByTagName("semantic:messageFlow"):
            if (messageFlow.getAttribute("targetRef") == flowObjectID):
                messageID = messageFlow.getAttribute("messageRef")
                requiredMessages.add(messageID)

        # Collect the IDs of data stores and data objects required by this vertex
        requiredDataStores = set()
        requiredDataObjects = set()
        children = getChildren(flowObject)
        for child in children:
            if (child.tagName == "semantic:dataInputAssociation"):
                associationChildren = getChildren(child)
                for associationChild in associationChildren:
                    if (associationChild.tagName == "semantic:sourceRef"):
                        dataStoreOrObjectReferenceID = associationChild.firstChild.nodeValue
                        dataStoreOrObjectReference = workflow.getElementById(dataStoreOrObjectReferenceID)
                        dataStoreOrObjectReferenceTagName = dataStoreOrObjectReference.tagName
                        if (dataStoreOrObjectReferenceTagName == "semantic:dataStoreReference"):
                            dataStoreID = dataStoreOrObjectReference.getAttribute("dataStoreRef")
                            requiredDataStores.add(dataStoreID)
                        elif (dataStoreOrObjectReferenceTagName == "semantic:dataObjectReference"):
                            dataObjectID = dataStoreOrObjectReference.getAttribute("dataObjectRef")
                            requiredDataObjects.add(dataObjectID)
                        else:
                            raise UnsupportedOperation("Unsupported data object with tag (" + dataStoreOrObjectReferenceTagName + ")")

        # Collect the IDs of messages produced by this vertex
        producedMessages = set()
        for messageFlow in workflow.getElementsByTagName("semantic:messageFlow"):
            if (messageFlow.getAttribute("sourceRef") == flowObjectID):
                messageID = messageFlow.getAttribute("messageRef")
                producedMessages.add(messageID)
        
        # Collect the IDs of data stores and objects produced by this vertex
        producedDataStores = set()
        producedDataObjects = set()
        children = getChildren(flowObject)
        for child in children:
            if (child.tagName == "semantic:dataOutputAssociation"):
                associationChildren = getChildren(child)
                for associationChild in associationChildren:
                    if (associationChild.tagName == "semantic:targetRef"):
                        dataStoreOrObjectReferenceID = associationChild.firstChild.nodeValue
                        dataStoreOrObjectReference = workflow.getElementById(dataStoreOrObjectReferenceID)
                        dataStoreOrObjectReferenceTagName = dataStoreOrObjectReference.tagName
                        if (dataStoreOrObjectReferenceTagName == "semantic:dataStoreReference"):
                            dataStoreID = dataStoreOrObjectReference.getAttribute("dataStoreRef")
                            producedDataStores.add(dataStoreID)
                        elif (dataStoreOrObjectReferenceTagName == "semantic:dataObjectReference"):
                            dataObjectID = dataStoreOrObjectReference.getAttribute("dataObjectRef")
                            producedDataObjects.add(dataObjectID)
                        else:
                            raise UnsupportedOperation("Unsupported data object with tag (" + dataStoreOrObjectReferenceTagName + ")")

        graph.addVertex(
            id=flowObjectID,
            name=flowObjectName,
            pool=getPoolOfElementID(workflow, flowObjectID), 
            lane=getLaneOfElementID(workflow, flowObjectID), 
            vertexType=getFlowObjectType(flowObject),
            requiredMessages=requiredMessages,
            producedMessages=producedMessages,
            requiredDataStores=requiredDataStores,
            producedDataStores=producedDataStores,
            requiredDataObjects=requiredDataObjects,
            producedDataObjects=producedDataObjects,
            partiallyExplored=False
        )

logging.info("Print info")
graph.printInfo()

logging.info("Print the vertices")
graph.printVertices()

logging.info("Print the edges")
graph.printEdges()

logging.info("Build the graph")
graph.buildGraph()
#graph.printGraph()

logging.info("Print the loops")
loops = graph.findLoops()
logging.info(loops)

logging.info("Marking edges and vertices in loops")
graph.markEdgesAndVerticesInLoops(loops)
logging.info("===== ===== ===== ===== ===== ===== end 2 ===== ===== ===== ===== ===== =====")
# ===== ===== ===== ===== ===== ===== end 2 ===== ===== ===== ===== ===== ===== 




















# ===== ===== ===== ===== ===== ===== start 3 ===== ===== ===== ===== ===== ===== 
# Compute all possible paths (i.e., visit orders of Flow Objects) satisfying the workflow
logging.info("===== ===== ===== ===== ===== ===== start 3 ===== ===== ===== ===== ===== =====")


# At the beginning, the set of paths is composed of
# one path for each start event
paths = []
finishedPaths = []
discardedPaths = []
numberOfPaths = 0
numberOfGroups = 1



# Collect all messages, data stores and data objects which 
# are required by a task but are not produced by a previously
# executed task (i.e., external input). We need to produce 
# such resources a-priori.
messagesToProduceAPriori = set()
dataObjectsToProduceAPriori = set()
dataStoresToProduceAPriori = set()
requiredMessages = set()
producedMessages = set()
requiredDataStores = set()
producedDataStores = set()
requiredDataObjects = set()
producedDataObjects = set()
for vertex in graph.getVertices():
    for requiredMessage in vertex.getRequiredMessages():
        requiredMessages.add(requiredMessage)
    for produceMessage in vertex.getProducedMessages():
        producedMessages.add(produceMessage)
    for requiredDataStore in vertex.getRequiredDataStores():
        requiredDataStores.add(requiredDataStore)
    for producedDataStore in vertex.getProducedDataStores():
        producedDataStores.add(producedDataStore)
    for requiredDataObject in vertex.getRequiredDataObjects():
        requiredDataObjects.add(requiredDataObject)
    for producedDataObject in vertex.getProducedDataObjects():
        producedDataObjects.add(producedDataObject)
messagesToProduceAPriori = requiredMessages - producedMessages
dataStoresToProduceAPriori = requiredDataStores.union(producedDataStores)  # We assume data stores to exist already
dataObjectsToProduceAPriori = requiredDataObjects - producedDataObjects
if (len(messagesToProduceAPriori) > 0):
    logging.info("There are " + str(len(messagesToProduceAPriori)) + " messages to produce a-priori (see below for IDs)")
    logging.info(messagesToProduceAPriori)
if (len(dataStoresToProduceAPriori) > 0):
    logging.info("There are " + str(len(dataStoresToProduceAPriori)) + " data stores to produce a-priori (see below for IDs)")
    logging.info(dataStoresToProduceAPriori)
if (len(dataObjectsToProduceAPriori) > 0):
    logging.info("There are " + str(len(dataObjectsToProduceAPriori)) + " data objects to produce a-priori (see below for IDs)")
    logging.info(dataObjectsToProduceAPriori)






startEventIDs = getAllStartEventsID(workflow)
logging.info("There are " + str(len(startEventIDs)) + " start events (see below for IDs)")
logging.info(startEventIDs)
for startEventID in startEventIDs:
    # If we are not interested in computing all paths, 
    # we can stop after one path (which contains all
    # of the start events anyway)
    if (not computeAllExecutions and numberOfPaths == 1):
        break

    numberOfPaths = numberOfPaths + 1
    currentPath = BPMNPath(logging, numberOfPaths, numberOfGroups)
    currentPath.addVertexToExplore(graph.getVertexByID(startEventID))
    for nextStartEventID in startEventIDs:
        if (startEventID != nextStartEventID):
            currentPath.addVertexToExplore(graph.getVertexByID(nextStartEventID))

    # Produce messages, data stores and data objects to produce a-priori
    for messageToProduceAPriori in messagesToProduceAPriori:
        currentPath.addMessageProduced(messageToProduceAPriori)
    for dataStoreToProduceAPriori in dataStoresToProduceAPriori:
        currentPath.addDataStoreProduced(dataStoreToProduceAPriori)
    for dataObjectToProduceAPriori in dataObjectsToProduceAPriori:
        currentPath.addDataObjectProduced(dataObjectToProduceAPriori)

    paths.append(currentPath)

# While there is at least one 
# path that has still to finish
while (paths):

    createPermutationsOnNextRound = False
    currentPath = paths[0]       
    currentPathGroupAndID = currentPath.getGroupAndID()
    paths.pop(0)

    logging.info("Path "
        + currentPathGroupAndID
        + ": starting the analysis (there are still "
        + str(len(paths)) 
        + " paths to examine)"
        )

    # Until the currentPath is not finished
    while (not currentPath.isFinished()):

        currentVertex = currentPath.popVertexToExplore()
        currentVertexType = currentVertex.vertexType

        logging.debug("Path " 
            + currentPathGroupAndID
            + ": visiting Flow Object of type " 
            + str(currentVertexType) 
            + ", id or name is '" 
            + currentVertex.getNameOrTypeAndID()
            + "'"
        )

        # If the vertex is an intermediate vertex (i.e., not an
        # end event), add all outgoing Connecting Objects to the 
        # set of vertices to explore
        if (
            currentVertexType == FlowObjects.StartEvent or
            currentVertexType == FlowObjects.Task or 
            currentVertexType == FlowObjects.ManualTask or 
            currentVertexType == FlowObjects.SendTask or 
            currentVertexType == FlowObjects.ReceiveTask or 
            currentVertexType == FlowObjects.UserTask or 
            currentVertexType == FlowObjects.IntermediateCatchEvent or
            currentVertexType == FlowObjects.ParallelGateway or
            currentVertexType == FlowObjects.ExclusiveGateway or
            currentVertexType == FlowObjects.EventBasedGateway or
            currentVertexType == FlowObjects.MessageStartEvent or
            currentVertexType == FlowObjects.MessageIntermediateCatchEvent
        ):

            # Explore this vertex only if all 
            # required messages, data stores
            # and data objects were already 
            # produced
            messagesProduced = currentPath.getMessagesProduced()
            dataStoresProduced = currentPath.getDataStoresProduced()
            dataObjectsProduced = currentPath.getDataObjectsProduced()
            if (all(x in messagesProduced for x in currentVertex.getRequiredMessages())
                and
                all(x in dataStoresProduced for x in currentVertex.getRequiredDataStores())
                and
                all(x in dataObjectsProduced for x in currentVertex.getRequiredDataObjects())
            ):
                currentPath.addVertexExplored(currentVertex)

                # If we have an exclusive gateway, we need to split 
                # the path and take one and one only of the outgoing
                # edges. Then, we create all permutations
                if (currentVertexType == FlowObjects.ExclusiveGateway):
                    outgoingEdges = graph.getEdgesBySourceID(currentVertex.id)
                    for outgoingEdge in outgoingEdges:
                        clonedPathDifferentGroup = currentPath.deepClone()
                        clonedPathDifferentGroup.setGroup(numberOfGroups)
                        numberOfGroups = numberOfGroups + 1
                        clonedPathDifferentGroup.addVertexToExplore(graph.getVertexByID(outgoingEdge.targetID))
                        clonedPathDifferentGroup.addEdgeExplored(outgoingEdge)
                        clonedPathGroupAndID = clonedPathDifferentGroup.getGroupAndID()

                        # Create all permutations
                        verticesToExploreInClonedPath = clonedPathDifferentGroup.getVerticesToExplore()
                        numberOfPathsInNewGroup = 0
                        for vertexToExploreInClonedPath in verticesToExploreInClonedPath:
                            clonedPathSameGroup = clonedPathDifferentGroup.deepClone()
                            numberOfPathsInNewGroup = numberOfPathsInNewGroup + 1
                            numberOfPaths = numberOfPaths + 1
                            clonedPathSameGroup.setID(numberOfPaths)
                            cloneVerticesToExplore = clonedPathSameGroup.getVerticesToExplore()
                            cloneVerticesToExplore.remove(vertexToExploreInClonedPath)
                            cloneVerticesToExplore.insert(0, vertexToExploreInClonedPath)
                            clonedPathSameGroup.setVerticesToExplore(cloneVerticesToExplore)
                            paths.append(clonedPathSameGroup)
                        logging.info("Path " 
                            + clonedPathGroupAndID
                            + ": created " 
                            + str(numberOfPathsInNewGroup) 
                            + " paths as result of new group (IDs are same group from " 
                            + str(numberOfPaths-numberOfPathsInNewGroup+1)
                            + " to "
                            + str(numberOfPaths)
                            + ")"
                        )
                    # We break, because the current path created different 
                    # groups, each with a different set of vertices to explore,
                    # and we already created all permutations for the paths 
                    # in the new group
                    break




                # For all other types of gateways, instead, explore 
                # all outgoing edges and proceeed with the visit of 
                # the current path
                else:
                    createPermutationsOnNextRound = True
                    outgoingEdges = graph.getEdgesBySourceID(currentVertex.id)
                    for outgoingEdge in outgoingEdges:
                        currentPath.addVertexToExplore(graph.getVertexByID(outgoingEdge.targetID))
                        currentPath.addEdgeExplored(outgoingEdge)
                    

            # Else, not all required messages 
            # or data stores or data objects 
            # were produced
            else:
                logging.info("Path " 
                    + currentPathGroupAndID
                    + ": vertex " 
                    + currentVertex.getNameOrTypeAndID()
                    + ", not all required messages or data stores or data objects were produced."
                    + " Messages required "
                    + str(currentVertex.getRequiredMessages())
                    + ", available messages "
                    + str(messagesProduced)
                    + ". Data stores required "
                    + str(currentVertex.getRequiredDataStores())
                    + ", available data stores "
                    + str(dataStoresProduced)
                    + ". Data objects required "
                    + str(currentVertex.getRequiredDataObjects())
                    + ", available data objects "
                    + str(dataObjectsProduced)
                    + ". For now, produce only messages, data stores and data objects coming before the required ones"
                )
                atLeastAResourceWasProduced = False

                # Below, we read from the workflow XML file the messages, the
                # data stores and the data objects in the order as they are written
                workflowOrderedResourcesIDs = []
                with open(workflowXML) as f:
                    workflowString = f.read()
                    
                    partialMessages = re.findall('<semantic:message (.+?)/>', workflowString)
                    partialDataStores = re.findall('<semantic:dataStore (.+?)/>', workflowString)
                    partialDataObjects = re.findall('<semantic:dataObject (.+?)/>', workflowString)
                    messages = []
                    dataStores = []
                    dataObjects = []
                    for partialMessage in partialMessages:
                        messages.append("<semantic:message " + partialMessage + "/>")
                    for partialDataStore in partialDataStores:
                        dataStores.append("<semantic:dataStore " + partialDataStore + "/>")
                    for partialDataObject in partialDataObjects:
                        dataObjects.append("<semantic:dataObject " + partialDataObject + "/>")

                    while (len(messages) != 0 or len(dataStores) != 0 or len(dataObjects) != 0):
                        if (len(messages) != 0):
                            firstMessageIndex = workflowString.index(messages[0])
                        else:
                            firstMessageIndex = float('inf')
                        if (len(dataStores) != 0):
                            firstDataStoreIndex = workflowString.index(dataStores[0])
                        else:
                            firstDataStoreIndex = float('inf')
                        if (len(dataObjects) != 0):
                            firstDataObjectIndex = workflowString.index(dataObjects[0])
                        else:
                            firstDataObjectIndex = float('inf')

                        if (firstMessageIndex == min(firstMessageIndex, firstDataStoreIndex, firstDataObjectIndex)):
                            workflowOrderedResourcesIDs.append(
                                re.search('id="(.+?)"', messages[0]).group(1)
                            )
                            messages.pop(0)
                        elif (firstDataStoreIndex == min(firstMessageIndex, firstDataStoreIndex, firstDataObjectIndex)):
                            workflowOrderedResourcesIDs.append(
                                re.search('id="(.+?)"', dataStores[0]).group(1)
                            )
                            dataStores.pop(0)
                        elif (firstDataObjectIndex == min(firstMessageIndex, firstDataStoreIndex, firstDataObjectIndex)):
                            workflowOrderedResourcesIDs.append(
                                re.search('id="(.+?)"', dataObjects[0]).group(1)
                            )
                            dataObjects.pop(0)
                            
                logging.debug("The ordered list of messages, data stores and data objects IDs is (see below)")                            
                logging.debug(workflowOrderedResourcesIDs)

                producedMessageIDs = set()
                producedDataStoreIDs = set()
                producedDataObjectIDs = set()
                producedMessageID = None
                producedDataStoreID = None
                producedDataObjectID = None
                canWeProduceMessage = False
                canWeProduceDataStore = False
                canWeProduceDataObject = False
                for workflowOrderedResourceIDs in workflowOrderedResourcesIDs:
                    if workflowOrderedResourceIDs in currentVertex.getProducedMessages():
                        producedMessageID = workflowOrderedResourceIDs
                        canWeProduceMessage = True
                        break
                    elif workflowOrderedResourceIDs in currentVertex.getProducedDataStores():
                        producedDataStoreID = workflowOrderedResourceIDs
                        canWeProduceDataStore = True
                        break
                    elif workflowOrderedResourceIDs in currentVertex.getProducedDataObjects():
                        producedDataObjectID = workflowOrderedResourceIDs
                        canWeProduceDataObject = True
                        break
                    elif (
                        (
                            workflowOrderedResourceIDs not in currentPath.getMessagesProduced()
                            and
                            workflowOrderedResourceIDs not in currentPath.getDataStoresProduced()
                            and
                            workflowOrderedResourceIDs not in currentPath.getDataObjectsProduced()
                        )
                        and
                        (
                            workflowOrderedResourceIDs in currentVertex.getRequiredMessages()
                            or
                            workflowOrderedResourceIDs in currentVertex.getRequiredDataStores()
                            or
                            workflowOrderedResourceIDs in currentVertex.getRequiredDataObjects()
                        )
 
                         ):
                         logging.debug("Resource " + 
                             workflowOrderedResourceIDs + 
                             " was not produced but it is required"
                         )         
                         break


                if (canWeProduceMessage):
                    logging.info("Path " 
                        + currentPathGroupAndID
                        + ": vertex " 
                        + currentVertex.getNameOrTypeAndID()
                        + " is producing partial message '"
                        + producedMessageID
                        + "'"
                    )
                    atLeastAResourceWasProduced = True
                    producedMessageIDs.add(producedMessageID)
                elif (canWeProduceDataStore):
                    logging.info("Path " 
                        + currentPathGroupAndID
                        + ": vertex " 
                        + currentVertex.getNameOrTypeAndID()
                        + " is producing partial data store '"
                        + producedDataStoreID
                        + "'"
                    )
                    atLeastAResourceWasProduced = True
                    producedDataStoreIDs.add(producedDataStoreID)
                elif (canWeProduceDataObject):
                    logging.info("Path " 
                        + currentPathGroupAndID
                        + ": vertex " 
                        + currentVertex.getNameOrTypeAndID()
                        + " is producing partial data object '"
                        + producedDataObjectID
                        + "'"
                    )
                    atLeastAResourceWasProduced = True
                    producedDataObjectIDs.add(producedDataObjectID)

                    
                # If we are computing all paths but in this path no vertex
                # was explored and no message or data store or data object
                # was produced, we can stop this path, as for sure there is 
                # another path which would have now the same list of vertices 
                # to explore as this path
                if (computeAllExecutions and not atLeastAResourceWasProduced):
                    logging.info("Path " 
                        + currentPathGroupAndID
                        + ": vertex " 
                        + currentVertex.getNameOrTypeAndID()
                        + " produced no message nor data store nor data object"
                    )
                    break
                # Else, mark the vertex as "partially visited", put it back 
                # into the list of vertices to explore and proceed
                else:
                    createPermutationsOnNextRound = True

                    partialCurrentVertex = currentVertex.deepClone()
                    partialCurrentVertex.setRequiredMessages(currentVertex.getRequiredMessages() & set(messagesProduced))
                    partialCurrentVertex.setRequiredDataStores(currentVertex.getRequiredDataStores() & set(dataStoresProduced))
                    partialCurrentVertex.setRequiredDataObjects(currentVertex.getRequiredDataObjects() & set(dataObjectsProduced))
                    partialCurrentVertex.setProducedMessages(producedMessageIDs)
                    partialCurrentVertex.setProducedDataStores(producedDataStoreIDs)
                    partialCurrentVertex.setProducedDataObjects(producedDataObjectIDs)
                    partialCurrentVertex.setPartiallyExplored(True)
                    currentPath.addVertexExplored(partialCurrentVertex)

                    currentVertex.setRequiredMessages(currentVertex.getRequiredMessages() - set(messagesProduced))
                    currentVertex.setRequiredDataStores(currentVertex.getRequiredDataStores() - set(dataStoresProduced))
                    currentVertex.setRequiredDataObjects(currentVertex.getRequiredDataObjects() - set(dataObjectsProduced))
                    currentVertex.setProducedMessages(currentVertex.getProducedMessages() - producedMessageIDs)
                    currentVertex.setProducedDataStores(currentVertex.getProducedDataStores() - producedDataStoreIDs)
                    currentVertex.setProducedDataObjects(currentVertex.getProducedDataObjects() - producedDataObjectIDs)
                    currentPath.addVertexToExplore(currentVertex)


        # If we reach an end event for a pool:
        # 1. assert that there are no outgoing edges
        #    nor required messages nor data stores nor data objects;
        # 2. remove from the vertices to explore next 
        #    all vertices belonging to the pool.
        # 3. if what remains in the vertices to explore
        #    are start events only AND those start events
        #    are requiring resources which were not produced,
        #    then it means that we can save this path, because
        #    it is valid as it is
        elif (currentVertexType == FlowObjects.EndEvent):
            assert len(graph.getEdgesBySourceID(currentVertex.id)) == 0
            assert len(currentVertex.getRequiredMessages()) == 0
            assert len(currentVertex.getRequiredDataStores()) == 0
            assert len(currentVertex.getRequiredDataObjects()) == 0
            currentPath.addVertexExplored(currentVertex)
            
            endEventPool = currentVertex.pool
            verticesStillToExplore = []
            areThereStartEventsOnly = True
            for vertexToExplore in currentPath.getVerticesToExplore():
                if (vertexToExplore.pool != endEventPool):
                    verticesStillToExplore.append(vertexToExplore)
                    if (
                        vertexToExplore.vertexType != FlowObjects.StartEvent
                        and
                        vertexToExplore.vertexType != FlowObjects.MessageStartEvent
                    ):
                        areThereStartEventsOnly = False

            if (areThereStartEventsOnly):
                allStartEventsCannotBeVisited = True    
                for startEvent in verticesStillToExplore:
                    if (all(x in currentPath.getMessagesProduced() for x in startEvent.getRequiredMessages())
                        and
                        all(x in currentPath.getDataStoresProduced() for x in startEvent.getRequiredDataStores())
                        and
                        all(x in currentPath.getDataObjectsProduced() for x in startEvent.getRequiredDataObjects())
                    ):
                        allStartEventsCannotBeVisited = False
                        break

            if (areThereStartEventsOnly and allStartEventsCannotBeVisited):
                currentPath.setVerticesToExplore([])
                createPermutationsOnNextRound = False
            else:
                currentPath.setVerticesToExplore(verticesStillToExplore)
                createPermutationsOnNextRound = True


        # Else, we have an unsupported Flow Object
        else:
            raise UnsupportedOperation("UnsupportedFlowObject (" + currentVertexType + ")")

        # For each possible next vertex to explore, 
        # add a cloned path (same group), if not 
        # already present, which starts from that 
        # vertex. Do NOT compute all possible 
        # permutations on all nodes (just the first
        # one), otherwise it becomes redundant
        if (computeAllExecutions):
            numberOfPathsCreatedInThisRound = 0
            if (createPermutationsOnNextRound):
                verticesToExploreInCurrentPath = currentPath.getVerticesToExplore()
                for vertexToExploreInCurrentPath in verticesToExploreInCurrentPath[1:]:
                    clonedPathSameGroup = currentPath.deepClone()
                    if (clonedPathSameGroup not in paths):
                        numberOfPathsCreatedInThisRound = numberOfPathsCreatedInThisRound + 1
                        numberOfPaths = numberOfPaths + 1
                        clonedPathSameGroup.setID(numberOfPaths)
                        cloneVerticesToExplore = clonedPathSameGroup.getVerticesToExplore()
                        cloneVerticesToExplore.remove(vertexToExploreInCurrentPath)
                        cloneVerticesToExplore.insert(0, vertexToExploreInCurrentPath)
                        clonedPathSameGroup.setVerticesToExplore(cloneVerticesToExplore)
                        paths.append(clonedPathSameGroup)
                logging.debug("Path " 
                    + currentPathGroupAndID
                    + ": adding " 
                    + str(numberOfPathsCreatedInThisRound) 
                    + " paths as result of permutations (IDs are same group from " 
                    + str(numberOfPaths-numberOfPathsCreatedInThisRound+1)
                    + " to "
                    + str(numberOfPaths)
                    + ")"
                )
            else:
                logging.debug("Path " 
                    + currentPathGroupAndID
                    + ": not creating any permutation this round" 
                )
            createPermutationsOnNextRound = False



    # Add the path only if it has finished (e.g., the path
    # did not stop because "not atLeastAResourceWasProduced" in
    # a moment of the visit of the graph)
    if (currentPath.isFinished()):
        logging.info("Path " + currentPath.getGroupAndID() + " finished, appending to list of finished paths")
        finishedPaths.append(currentPath)
    else:
        assert(computeAllExecutions)
        logging.warning("Discarding path " + currentPathGroupAndID + " as duplicated")
        discardedPaths.append(currentPathGroupAndID)


logging.info("Path analysis concluded. We found " 
    + str(len(finishedPaths)) 
    + " paths and discarded "
    + str(len(discardedPaths)) 
    + " paths"
)

for path in finishedPaths:
    logging.debug("Path " + path.getGroupAndID())
    path.printToLogVertices()
logging.info("===== ===== ===== ===== ===== ===== end 3 ===== ===== ===== ===== ===== =====")
# ===== ===== ===== ===== ===== ===== end 3 ===== ===== ===== ===== ===== ===== 



















# ===== ===== ===== ===== ===== ===== start 4 ===== ===== ===== ===== ===== ===== 
# Translate each path into a list of AC operations and write the obtained lists into a JSON file
logging.info("===== ===== ===== ===== ===== ===== start 4 ===== ===== ===== ===== ===== =====")
def assignPermission(vertexNameOrID, resourceName, roleName, permission, type, measure = True):
    op = (
        "        { \"vertex\":\"" 
        + vertexNameOrID.replace(" ", "_") 
        + "\", \"op\":\"assignPermission\", \"resourceName\":\"" 
        + resourceName.replace(" ", "_") 
        + "\", \"roleName\":\"" 
        + roleName.replace(" ", "_") 
        + "\", \"permission\":\"" 
        + permission.replace(" ", "_") 
        + "\", \"type\":\"" 
        + type 
        + "\", \"measure\":" 
        + str(measure).lower()
        + "},\n"
    )
    return op

def deleteResource(vertexNameOrID, resourceName, type, measure = True):
    op = (
        "        { \"vertex\":\"" 
        + vertexNameOrID.replace(" ", "_") 
        + "\", \"op\":\"deleteResource\", \"resourceName\":\"" 
        + resourceName.replace(" ", "_") 
        + "\", \"type\":\"" 
        + type 
        + "\", \"measure\":" 
        + str(measure).lower()
        + "},\n"
    )
    return op

def revokePermission(vertexNameOrID, resourceName, roleFromWhichRevoke, permission, type, measure = True):
    op = (
        "        { \"vertex\":\"" 
        + vertexNameOrID.replace(" ", "_") 
        + "\", \"op\":\"revokePermission\", \"resourceName\":\"" 
        + resourceName.replace(" ", "_") 
        + "\", \"roleName\":\"" 
        + roleFromWhichRevoke.replace(" ", "_") 
        + "\", \"permission\":\"" 
        + permission
        + "\", \"type\":\"" 
        + type 
        + "\", \"measure\":" 
        + str(measure).lower()
        + "},\n"
    )
    return op

def readResource(vertexNameOrID, resourceName, roleAssumed, type, measure = True):
    op = (
        "        { \"vertex\":\"" 
        + vertexNameOrID.replace(" ", "_") 
        + "\", \"op\":\"readResource\", \"resourceName\":\"" 
        + resourceName.replace(" ", "_") 
        + "\", \"roleName\":\"" 
        + roleAssumed.replace(" ", "_") 
        + "\", \"type\":\"" 
        + type 
        + "\", \"measure\":" 
        + str(measure).lower()
        + "},\n"
    )
    return op

def addResource(vertexNameOrID, resourceName, roleAssumed, size, type, measure = True):
    op = (
        "        { \"vertex\":\"" 
        + vertexNameOrID.replace(" ", "_") 
        + "\", \"op\":\"addResource\", \"resourceName\":\"" 
        + resourceName.replace(" ", "_") 
        + "\", \"roleName\":\"" 
        + roleAssumed.replace(" ", "_") 
        + "\", \"type\":\"" 
        + type 
        + "\", \"resourceSize\":" 
        + str(size)
        + ", \"measure\":" 
        + str(measure).lower()
        + "},\n"

    )
    return op

def writeResource(vertexNameOrID, resourceName, roleAssumed, size, type, measure = True):
    op = (
        "        { \"vertex\":\"" 
        + vertexNameOrID.replace(" ", "_") 
        + "\", \"op\":\"writeResource\", \"resourceName\":\"" 
        + resourceName.replace(" ", "_") 
        + "\", \"roleName\":\"" 
        + roleAssumed.replace(" ", "_") 
        + "\", \"type\":\"" 
        + type 
        + "\", \"resourceSize\":" 
        + str(size)
        + ", \"measure\":" 
        + str(measure).lower()
        + "},\n"

    )
    return op

def addRole(vertexNameOrID, roleName, measure = True):
    op = (
        "        { \"vertex\":\"" 
        + vertexNameOrID.replace(" ", "_") 
        + "\", \"op\":\"addRole\", \"roleName\":\"" 
        + roleName.replace(" ", "_") 
        + "\", \"measure\":" 
        + str(measure).lower()
        + "},\n"
    )
    return op

def deleteRole(vertexNameOrID, roleName, measure = True):
    op = (
        "        { \"vertex\":\"" 
        + vertexNameOrID.replace(" ", "_") 
        + "\", \"op\":\"deleteRole\", \"roleName\":\"" 
        + roleName.replace(" ", "_") 
        + "\", \"measure\":" 
        + str(measure).lower()
        + "},\n"
    )
    return op


# This is the dict of AC operations obtained from parsing the paths. 
# The key is the pathID, the value is another dictionary with the 
# following key-value pairs:
# * "ops" - list of AC operations of the path (String)
# * "duplicatePathIDs" - list of Path IDs whose operations would have
#                        been the same as this one and, as such, were
#                        not included in the dict
# Later on, this dictionary will be saved in a JSON file
listOfPaths = {}

for path in finishedPaths:
    pathGroupAndID = path.getGroupAndID()
    logging.info("Path " + pathGroupAndID + ": translating")
    rolesForThisPath = {}
    dataStoresAlreadyExisting = []
    acOperationsString = ""


    # Create a-priori messages (do not measure the time
    # it will take to create these messages)
    for messageToProduceAPriori in messagesToProduceAPriori:
        acOperationsString = acOperationsString + addResource(
            "a-priori", 
            messageToProduceAPriori, 
            adminName, 
            1,
            "transient",
            False
        )

    # Create a-priori data objects (do not measure the time
    # it will take to create these data objects)
    for dataObjectToProduceAPriori in dataObjectsToProduceAPriori:
        acOperationsString = acOperationsString + addResource(
            "a-priori", 
            dataObjectToProduceAPriori, 
            adminName, 
            1,
            "transient",
            False
        )

    # Create a-priori data stores (do not measure the time
    # it will take to create these data stores)
    for dataStoreToProduceAPriori in dataStoresToProduceAPriori:
        acOperationsString = acOperationsString + addResource(
            "a-priori", 
            dataStoreToProduceAPriori, 
            adminName, 
            1,
            "persistent",
            False
        )
        dataStoresAlreadyExisting.append(dataStoreToProduceAPriori)


 

    # Now, parse each vertex of the path
    for vertex in path.getVerticesExplored():

        # Check whether we need to create a role 
        # before executing the vertex
        vertexNameOrID = vertex.getNameOrTypeAndID()
        if (vertex.pool not in rolesForThisPath):
            acOperationsString = acOperationsString + addRole(
                vertexNameOrID=vertexNameOrID, 
                roleName=vertex.lane
            )
            rolesForThisPath[vertex.pool] = [vertex.lane]
        else:
            if (vertex.lane not in rolesForThisPath[vertex.pool]):
                acOperationsString = acOperationsString + addRole(
                    vertexNameOrID=vertexNameOrID, 
                    roleName=vertex.lane
                )
                rolesForThisPath[vertex.pool].append(vertex.lane)


        # For each required message, assign the permission 
        # to read it to the role, then read it, finally delete 
        # it (messages are not persistent)
        for requiredMessage in vertex.getRequiredMessages():
            acOperationsString = acOperationsString + assignPermission(
                vertexNameOrID, 
                requiredMessage, 
                vertex.lane, 
                "READ",
                "transient"
            )
            acOperationsString = acOperationsString + readResource(
                vertexNameOrID,
                requiredMessage, 
                vertex.lane,
                "transient"
            )
            acOperationsString = acOperationsString + revokePermission(
                vertexNameOrID,
                requiredMessage, 
                vertex.lane,
                "READ",
                "transient"
            )
            acOperationsString = acOperationsString + deleteResource(
                vertexNameOrID,
                requiredMessage,
                "transient"
            )


        # For each required data object, assign the permission 
        # to read it to the role, then read it, finally delete 
        # it (data objects are not persistent)
        for requiredDataObject in vertex.getRequiredDataObjects():
            acOperationsString = acOperationsString + assignPermission(
                vertexNameOrID, 
                requiredDataObject, 
                vertex.lane, 
                "READ",
                "transient"
            )
            acOperationsString = acOperationsString + readResource(
                vertexNameOrID,
                requiredDataObject, 
                vertex.lane,
                "transient"
            )
            acOperationsString = acOperationsString + revokePermission(
                vertexNameOrID,
                requiredDataObject, 
                vertex.lane,
                "READ",
                "transient"
            )
            acOperationsString = acOperationsString + deleteResource(
                vertexNameOrID,
                requiredDataObject,
                "transient"
            )


        # For each required data store, assign the permission 
        # to read it to the role, then read it, then do not 
        # delete it (data stores are not transient)
        for requiredDataStore in vertex.getRequiredDataStores():
            acOperationsString = acOperationsString + assignPermission(
                vertexNameOrID, 
                requiredDataStore, 
                vertex.lane, 
                "READ",
                "persistent"
            )
            acOperationsString = acOperationsString + readResource(
                vertexNameOrID,
                requiredDataStore, 
                vertex.lane,
                "persistent"
            )
            acOperationsString = acOperationsString + revokePermission(
                vertexNameOrID,
                requiredDataStore, 
                vertex.lane,
                "READ",
                "persistent"
            )
        
        
        # For each produced message, add a resource
        for producedMessage in vertex.getProducedMessages():
            acOperationsString = acOperationsString + addResource(
                vertexNameOrID, 
                producedMessage, 
                vertex.lane, 
                1,
                "transient"
            )


        # For each produced data object, add a resource
        for producedDataObject in vertex.getProducedDataObjects():
            acOperationsString = acOperationsString + addResource(
                vertexNameOrID, 
                producedDataObject, 
                vertex.lane, 
                1,
                "transient"
            )


        # For each produced data store, assign permission and write on (if the
        # data store already exists) or add a resource (if the data store is new)
        for producedDataStore in vertex.getProducedDataStores():
            if (producedDataStore in dataStoresAlreadyExisting):
                acOperationsString = acOperationsString + assignPermission(
                    vertexNameOrID, 
                    producedDataStore, 
                    vertex.lane, 
                    "WRITE",
                    "persistent"
                )
                acOperationsString = acOperationsString + writeResource(
                    vertexNameOrID, 
                    producedDataStore, 
                    vertex.lane, 
                    1,
                    "persistent"
                )
                acOperationsString = acOperationsString + revokePermission(
                    vertexNameOrID,
                    producedDataStore, 
                    vertex.lane,
                    "WRITE",
                    "persistent"
                )
            else:
                acOperationsString = acOperationsString + addResource(
                    vertexNameOrID, 
                    producedDataStore, 
                    vertex.lane, 
                    1,
                    "persistent"
                )
                dataStoresAlreadyExisting.append(producedDataStore)



        # If the vertex is an EndEvent, we delete all 
        # roles in the pool/lane, as we do not need them anymore               
        if (vertex.vertexType == FlowObjects.EndEvent and vertex.pool in rolesForThisPath):
            for role in rolesForThisPath[vertex.pool]:
                acOperationsString = acOperationsString + deleteRole(
                    vertexNameOrID=vertexNameOrID, 
                    roleName=role
                )
            del rolesForThisPath[vertex.pool]

    # Remove the last two characters (i.e., ",\n")
    acOperationsString = acOperationsString[:-2]

    # Check that the obtained list of AC operations is 
    # not duplicate of another one already in the list
    duplicatePathID = None
    for alreadyParsedPathID in listOfPaths:
        if (listOfPaths[alreadyParsedPathID]["ops"] == acOperationsString):
            if (duplicatePathID == None):
                duplicatePathID = alreadyParsedPathID
                listOfPaths[alreadyParsedPathID]["duplicatePathIDs"] = (
                    listOfPaths[alreadyParsedPathID]["duplicatePathIDs"]
                    + "\""
                    + pathGroupAndID
                    + "\", "
                )
            else:
                message = "Two paths have duplicate AC operations but are both in the final list"
                logging.error(message)
                raise ValueError(message)

    if (duplicatePathID != None):
        logging.warning("Discarding AC operations of path " + pathGroupAndID + " as duplicated")
    else:
        currentPathDict = {
            "ops": acOperationsString,
            "duplicatePathIDs": ""
        }
        listOfPaths[pathGroupAndID] = currentPathDict


# Finally, parse the obtained dictionary into a JSON
listOfACOperationsString = ("{\"name\": \"" 
    + workflowName.replace(" ", "_") 
    + "\",\n \"numberOfPaths\": "
    + str(numberOfPaths)
    + ",\n \"numberOfDiscardedPaths\": "
    + str(len(discardedPaths))
    + ",\n \"numberOfValidPaths\": "
    + str(len(finishedPaths))
    + ",\n \"numberOfDistinctValidPaths\": "
    + str(len(listOfPaths))
    + ",\n"
)


listOfACOperationsString = listOfACOperationsString + " \"discardedPathIDs\":["
for discardedPath in discardedPaths:
    listOfACOperationsString = listOfACOperationsString + "\"" + discardedPath + "\", "
if (not (len(discardedPaths) == 0)):
    listOfACOperationsString = listOfACOperationsString[:-2]
listOfACOperationsString = listOfACOperationsString + "],\n"

listOfACOperationsString = listOfACOperationsString + " \"paths\":[\n"
for pathID in listOfPaths:
    listOfACOperationsString = (listOfACOperationsString 
        + "    {\"pathID\": \"" 
        + pathID 
        + "\",\n     \"duplicatePathIDs\":["
        + listOfPaths[pathID]["duplicatePathIDs"][:-2]
        + "],\n     \"ops\":[\n"
        + listOfPaths[pathID]["ops"]
        + "\n    ]},\n"
    )

# Remove the last two characters (i.e., ",\n")
listOfACOperationsString = listOfACOperationsString[:-2]
listOfACOperationsString = listOfACOperationsString + "\n]}"

with open(outputJSON + "/" + workflowName.replace(" ", "_") + "_ACE.json", 'w') as f:
    f.write(listOfACOperationsString)
logging.info("===== ===== ===== ===== ===== ===== end 4 ===== ===== ===== ===== ===== =====")
# ===== ===== ===== ===== ===== ===== end 4 ===== ===== ===== ===== ===== =====
