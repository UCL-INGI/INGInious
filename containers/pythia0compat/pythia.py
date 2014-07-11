import json
import sys
import shutil
import os
import resource
import subprocess
import stat
from os import listdir
from os.path import isfile, join
import xmltodict
import StringIO

def copytree(src, dst, symlinks=False, ignore=None):
    """ Custom copy tree to allow to copy into existing directories """
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)
            
def setlimits():
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60)) #TODO: set real limits

def setExecutable(filename):
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | stat.S_IEXEC)

#get input data
stdin = sys.stdin.read().strip('\0').strip()
data = json.loads(stdin)
input_data = data["input"]
limits = data["limits"]

os.mkdir("/tmp/work")

#Copy /ro/task (which is read-only) in /job. Everything will be executed there
shutil.copytree("/ro/task","/job")

if not os.path.exists("/job/input"):
    os.mkdir("/job/input")
os.symlink("/job/input","/tmp/work/input")
    
os.mkdir("/tmp/work/output")
os.mkdir("/tmp/log")

#Copy the libs needed by the tools
if os.path.exists("/job/lib"):
    copytree("/job/lib","/job/input/lib")
else:
    os.mkdir("/job/input/lib")
copytree("/pythia/lib","/job/input/lib")

#Launch everything
stdOutputData={"stdout":"","stderr":""}

#Parse the files
files = [ join("/job/input",f) for f in listdir("/job/input") if isfile(join("/job/input",f)) ]
cmd = ["python", "/pythia/pythia_input.py"]+files
p = subprocess.Popen(cmd, preexec_fn=setlimits, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = p.communicate(stdin)
stdOutputData["stdout"] = stdOutputData["stdout"]+"PARSE: "+stdout+"\n"
stdOutputData["stderr"] = stdOutputData["stderr"]+"PARSE: "+stderr+"\n"

#Put the input in the .out files (...)
for question in input_data:
    open("/tmp/work/output/"+question+".out","w").write(input_data[question])
    
if os.path.exists("/job/dataset.sh"):
    setExecutable("/job/dataset.sh")
    os.chdir("/job")
    p = subprocess.Popen(["/job/dataset.sh"], preexec_fn=setlimits, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    stdout, stderr = p.communicate()
    stdOutputData["stdout"] = stdOutputData["stdout"]+"DATASET: "+stdout+"\n"
    stdOutputData["stderr"] = stdOutputData["stderr"]+"DATASET: "+stderr+"\n"

os.chdir("/tmp/work")
if os.path.exists("/job/run.sh"):
    setExecutable("/job/run.sh")
    p = subprocess.Popen(["/job/run.sh"], preexec_fn=setlimits, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    stdout, stderr = p.communicate()
    stdOutputData["stdout"] = stdOutputData["stdout"]+"RUN: "+stdout+"\n"
    stdOutputData["stderr"] = stdOutputData["stderr"]+"RUN: "+stderr+"\n"

#Move some files
shutil.copytree("/tmp/work/output","/job/output/files")
open("/job/output/status","w").write("done")

os.chdir("/job")
setExecutable("/job/feedback.sh")
p = subprocess.Popen(["/job/feedback.sh"], preexec_fn=setlimits, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
p.wait()
stdout, stderr = p.communicate()
stdOutputData["stdout"] = stdOutputData["stdout"]+"FEEDBACK: "+stdout+"\n"
stdOutputData["stderr"] = stdOutputData["stderr"]+"FEEDBACK: "+stderr+"\n"


if os.path.exists("feedback.xml"):
    fileF = open("feedback.xml","r")
    feedback = xmltodict.parse(fileF.read())['feedback']
    text = (feedback["#text"] if "#text" in feedback else "") + (feedback["general"] if "general" in feedback else "")
    problems = {}
    if "question" in feedback and isinstance(feedback["question"],list):
        for question in feedback["question"]:
            if "#text" in question:
                problems = {question["@id"]: question["#text"]}
    elif "question" in feedback: #ordered dict
        if "#text" in feedback["question"]:
            problems = {feedback["question"]["@id"]: feedback["question"]["#text"]}
    print json.dumps({"result":("success" if feedback["verdict"] == "OK" else "failed"),"text":text,"problems":problems,"v0out":stdOutputData})
else:
    print json.dumps({"result":"crash","text":"The grader did not give any input","problems":{},"v0out":stdOutputData})

