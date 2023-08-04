from enum import Enum
import sys

# These are the supported Flow Objects
ConnectingObjects = Enum('ConnectingObjects', 'Sequence Message DataStore DataObject')

# Get the type of the connecting object
def getConnectingObjectType(connectingObject):
    returnType = None
    connectingObjectTagName = connectingObject.tagName
    if (connectingObjectTagName == "semantic:sequenceFlow"):
        returnType = ConnectingObjects.Sequence
    elif (connectingObjectTagName == "semantic:messageFlow"):
        returnType = ConnectingObjects.Message
    elif (connectingObjectTagName == "semantic:dataStore"):
        returnType = ConnectingObjects.DataStore
    elif (connectingObjectTagName == "semantic:dataObject"):
        returnType = ConnectingObjects.DataObject
    else:
        sys.exit('UnsupportedConnectingObject')
    return returnType