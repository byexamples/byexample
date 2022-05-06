#!/bin/bash
trap 'echo INT ; sleep 2 ; echo Bye' INT
echo Start
sleep 3
echo BOOM
