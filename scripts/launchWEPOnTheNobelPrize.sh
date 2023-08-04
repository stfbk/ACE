#!/bin/sh

python3 ../code/ACE.py \
    ../workflows/xml/The\ Nobel\ Prize.bpmn \
    ../workflows/operations/ \
    --logLevel=INFO \
    --logFile=theNoblePrize.log \
    --allExecutions
    
