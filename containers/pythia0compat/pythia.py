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
import tempfile
import time
import tarfile
import base64
import signal
import codecs

def copytree(src, dst, symlinks=False, ignore=None):
    """ Custom copy tree to allow to copy into existing directories """
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

def setDirectoryRights(path):
    os.chmod(path, 0o777)
    os.chown(path, 4242, 4242)
    for root, dirs, files in os.walk(path):  
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o777)
            os.chown(os.path.join(root, d), 4242, 4242)
        for f in files:
            os.chmod(os.path.join(root, f), 0o777)
            os.chown(os.path.join(root, f), 4242, 4242)
            
def setlimits():
    os.setgid(4242)
    os.setuid(4242)
    #Send a SIGXCPU after limits["time"], then a SIGKILL after limits["time"]+5
    resource.setrlimit(resource.RLIMIT_CPU, (limits["time"], limits["time"]+5))
    #Limit number of subprocesses
    resource.setrlimit(resource.RLIMIT_NPROC, (100, 100))
    
def setExecutable(filename):
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | stat.S_IEXEC)

def executeProcess(filename,stdinString):
    setExecutable(filename)
    stdin = tempfile.TemporaryFile()
    stdin.write(stdinString)
    stdin.seek(0)
    
    stdout = tempfile.TemporaryFile()
    stderr = tempfile.TemporaryFile()
    p = subprocess.Popen([filename], preexec_fn=setlimits, stdin=stdin, stdout=stdout, stderr=stderr)
    start = time.time()
    while p.poll() is None:
        time.sleep(0.2)
        if time.time()-start > limits["time"]*2:
            p.kill()
            raise Exception("Timeout")
    stdout.seek(0)
    stderr.seek(0)
    
    status = p.returncode-128
    if status == signal.SIGXCPU:
        raise Exception("Timeout")
    
    return stdout.read()+" RETURN VALUE/"+str(p.returncode)+"/", stderr.read()

def get_tarfile(source_dir):
    encoded_string = ''
    with tarfile.open('/job/output/files/archive.tgz', "w:gz") as tar:
        tar.add(source_dir, arcname='/', recursive=True)
        
    with open('/job/output/files/archive.tgz', "rb") as tar:
        encoded_string = base64.b64encode(tar.read())
        
    return encoded_string

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

#Set rights on some files
setDirectoryRights("/job")
setDirectoryRights("/tmp")
setDirectoryRights("/pythia")
setDirectoryRights("/tmp")

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
    codecs.open("/tmp/work/output/"+question+".out","w","utf-8").write(input_data[question])
setDirectoryRights("/tmp/work")

if os.path.exists("/job/dataset.sh"):
    os.chdir("/job")
    try:
        stdout, stderr = executeProcess("/job/dataset.sh", "")
    except:
        print json.dumps({"result":"crash","text":"Dataset.sh did a timeout","problems":{},"v0out":stdOutputData})
        exit()
    stdOutputData["stdout"] = stdOutputData["stdout"]+"DATASET: "+stdout+"\n"
    stdOutputData["stderr"] = stdOutputData["stderr"]+"DATASET: "+stderr+"\n"

os.chdir("/tmp/work")
if os.path.exists("/job/run.sh"):
    setExecutable("/job/run.sh")
    try:
        stdout, stderr = executeProcess("/job/run.sh", "")
    except:
        print json.dumps({"result":"timeout","text":"Your code did a timeout","problems":{},"v0out":stdOutputData})
        exit()
    stdOutputData["stdout"] = stdOutputData["stdout"]+"RUN: "+stdout+"\n"
    stdOutputData["stderr"] = stdOutputData["stderr"]+"RUN: "+stderr+"\n"

#Move some files
shutil.copytree("/tmp/work/output","/job/output/files")
open("/job/output/status","w").write("done")

setDirectoryRights("/job")
os.chdir("/job")
try:
    stdout, stderr = executeProcess("/job/feedback.sh", "")
except:
    print json.dumps({"result":"crash","text":"Feedback.sh did a timeout","problems":{},"v0out":stdOutputData})
    exit()
stdOutputData["stdout"] = stdOutputData["stdout"]+"FEEDBACK: "+stdout+"\n"
stdOutputData["stderr"] = stdOutputData["stderr"]+"FEEDBACK: "+stderr+"\n"

archivetosend=get_tarfile('/job/output/files')

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
    print json.dumps({"result":("success" if feedback["verdict"] == "OK" else "failed"),"text":text,"problems":problems,"v0out":stdOutputData, "archive":archivetosend})
else:
    print json.dumps({"result":"crash","text":"The grader did not give any input","problems":{},"v0out":stdOutputData, "archive":archivetosend})

