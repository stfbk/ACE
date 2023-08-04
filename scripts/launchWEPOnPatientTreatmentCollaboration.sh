#!/bin/sh

python3 ../code/ACE.py \
    ../workflows/xml/Patient\ Treatment\ -\ Collaboration.bpmn \
    ../workflows/operations/ \
    --logLevel=DEBUG \
    --logFile=thePatientTreatmentCollaboration.log \
    --allExecutions
    

