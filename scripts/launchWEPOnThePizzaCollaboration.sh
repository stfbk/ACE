#!/bin/sh

python3 ../code/ACE.py \
    ../workflows/xml/The\ Pizza\ Collaboration.bpmn \
    ../workflows/operations/ \
    --logLevel=INFO \
    --logFile=thePizzaCollaboration.log \
    --allExecutions
