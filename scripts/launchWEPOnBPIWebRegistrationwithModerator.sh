#!/bin/sh

python3 ../code/ACE.py \
    ../workflows/xml/BPI\ Web\ Registration\ with\ Moderator.bpmn \
    ../workflows/operations/ \
    --logLevel=DEBUG \
    --logFile=theBPIWebRegistrationWithModerator.log \
    --allExecutions
    

