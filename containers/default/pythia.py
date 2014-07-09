import json
import sys
import shutil
import os

#Copy /ro/task (which is read-only) in /task. Everything will be executed there
shutil.copytree("/ro/task","/task")

#Change directory to /task
os.chdir("/task")

#Parse input to return stupid output
input = json.loads(sys.stdin.readline())
problems = {}
for boxId in input:
    taskId = boxId.split("/")[0]
    problems[taskId] = str(input[boxId])
print json.dumps({"result":"failed","text":"In fact, it's working, but it's a test :D","problems":problems})