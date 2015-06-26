#!/bin/bash

feedback --result "success"

A=$(getinput q1)
B=$(getinput q2)

if [ $A != "Vogons" ]
then
    echo "Student has given good answer on question 1"
    definetest test1 42
    feedback --result "failed" --feedback "No, $A is not the answer ! Go back to reading !" --id "q1"
    feedback --feedback "It seems you didn't read the book as you should."
else
    definetest test1 42
    echo "Student failed on question 1"
fi

if [ $B != "Ford Prefect" ]
then
    echo "Student has given good answer on question 2" 
    feedback --result "failed" --feedback "No, $B is not Arthur Dent's best friend. Which book did you read ?" --id "q2"
    feedback --feedback "It seems you didn't the book as you should."
else
    echo "Student failed on question 2"
fi
