#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" Tool to test a particular task directly in container. It even allows to use any internal command (but run_student) """

import sys
import os
import argparse
import base64
import json
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import shutil

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(os.path.realpath(__file__))),'..','..'))
import inginious.common.custom_yaml as yaml


def check_pid(pid):
    """ Check For the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

def update_input_json(test_dir, problem_ids):
    data = {}
    for pid, is_file in problem_ids.iteritems():
        content = open(os.path.join(test_dir, 'input', *pid.split('/'))).read()
        if is_file:
            data[pid] = {'filename': 'filename.something', 'value': base64.b64encode(content)}
        else:
            data[pid] = content
    json.dump({"input":data,"limits":{}}, open(os.path.join(test_dir, '.internal', 'input', '__inputdata.json'), 'w'))

def update_output_yaml(test_dir):
    """ Put the internal json as yaml to ensure readability """
    f = open(os.path.join(test_dir, "feedback.yaml"), "w")
    if os.path.exists(os.path.join(test_dir, 'output', "__feedback.json")):
        yaml.dump(json.load(open(os.path.join(test_dir, 'output', "__feedback.json"), 'r')), stream=f)

def observer_process(parent_pid, test_dir, problem_ids):
    observers = []

    # Observer for input
    observer = Observer()
    observer.schedule(WatchDogProxy(lambda: update_input_json(test_dir, problem_ids)), path=os.path.join(test_dir, "input"))
    observer.start()
    observers.append(observer)

    # Observer for output
    observer = Observer()
    observer.schedule(WatchDogProxy(lambda: update_output_yaml(test_dir)), path=os.path.join(test_dir, "output"))
    observer.start()
    observers.append(observer)

    try:
        while check_pid(parent_pid):
            time.sleep(1)
    except KeyboardInterrupt:
        [observer.stop() for observer in observers]
    [observer.join() for observer in observers]

class WatchDogProxy(PatternMatchingEventHandler, object):
    patterns = ["*"]

    def __init__(self, proxy_func):
        self._proxy_func = proxy_func
        PatternMatchingEventHandler.__init__(self)

    def process(self, event):
        self._proxy_func()

    def on_modified(self, event):
        self.process(event)


def setDirectoryRights(path):
    os.chmod(path, 0o777)
    for root, dirs, files in os.walk(path):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o777)
        for f in files:
            os.chmod(os.path.join(root, f), 0o777)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("task", help="Path to the task directory to test")
    parser.add_argument("container", help="Container to start")
    parser.add_argument("--testdir", help="Dir in which the tester will store its files. Default: './tests'", default="./tests")
    args = parser.parse_args()

    if not os.path.exists(args.testdir):
        os.mkdir(args.testdir)

    test_dir_number = 0
    while(True):
        if not os.path.exists(os.path.join(args.testdir, str(test_dir_number))):
            os.mkdir(os.path.join(args.testdir, str(test_dir_number)))
            break
        else:
            test_dir_number += 1

    test_dir = os.path.join(args.testdir, str(test_dir_number))

    for folder in ["input", "output", "tests", ".internal", ".internal/input"]:
        os.mkdir(os.path.join(test_dir, folder))

    shutil.copytree(args.task, os.path.join(test_dir, "task"))
    if not os.path.exists(os.path.join(test_dir, "task", "student")):
        os.mkdir(os.path.join(test_dir, "task", "student"))
    setDirectoryRights(os.path.join(test_dir, "task"))

    run_student = open(os.path.join(test_dir, '.internal', 'run_student'), 'w')
    run_student.write('#! /bin/bash\n')
    run_student.write("echo 'The run_student command is not available inside the task tester.'\n")
    run_student.write("echo 'You can either re-run the command without prefixing it with run_student or start manually another container, "
                      "with the following command:'\n")
    run_student.write("echo '$ docker run -ti --rm -v "+
                      os.path.abspath(os.path.join(test_dir, "task", "student"))+
                      ":/student CONTAINER_NAME YOUR_COMMAND'\n")
    run_student.close()

    os.chmod(os.path.join(test_dir, '.internal', 'run_student'), 0o777)

    problem_ids = {}
    try:
        data = yaml.load(open(os.path.join(args.task, 'task.yaml')))["problems"]
        for key, value in data.iteritems():
            if value["type"] == "code" and "boxes" in value:
                for box in value["boxes"]:
                    if value["boxes"][box]["type"] not in ["text", "file"]:
                        problem_ids[key+"/"+box] = False
                    elif value["boxes"][box]["type"] == "file":
                        problem_ids[key + "/" + box] = True
            elif value["type"] == "code-file":
                problem_ids[key] = True
            else:
                problem_ids[key] = False
    except:
        print "Cannot read task.yaml!"
        exit(1)

    for pid in problem_ids:
        todo = pid.split('/')
        if len(todo) == 2:
            if not os.path.exists(os.path.join(test_dir, "input", todo[0])):
                os.mkdir(os.path.join(test_dir, "input", todo[0]))
            open(os.path.join(test_dir, "input", todo[0], todo[1]), 'w')
        else:
            open(os.path.join(test_dir, "input", todo[0]), 'w')

    print "----------------------------------------------------------"
    print ""
    print "Put your input for the task in the folder {}.".format(os.path.join(test_dir, "input"))
    print "They will be available via the commands getinput and parsetemplate inside the container."
    print "The output of the container will be available in the folder {}.".format(os.path.join(test_dir, "output"))
    print "The archive made via the `archive` command inside the container are available in the folder {}.".format(os.path.join(test_dir, "archive"))
    print ""
    print "I will now start the container."
    print ""
    print "----------------------------------------------------------"

    update_input_json(test_dir, problem_ids)
    update_output_yaml(test_dir)

    parent_pid = os.getpid()

    pid = os.fork()
    if pid == 0:
        observer_process(parent_pid, test_dir, problem_ids)
        exit(0)

    os.execlp('docker',
              'docker',
              'run',
              '-t',
              '-i',
              '--rm',
              '-v',
              os.path.abspath(os.path.join(test_dir, ".internal", "input")) + ":/.__input",
              '-v',
              os.path.abspath(os.path.join(test_dir, "output")) + ":/.__output",
              '-v',
              os.path.abspath(os.path.join(test_dir, "tests")) + ":/.__tests",
              '-v',
              os.path.abspath(os.path.join(test_dir, "task"))+":/task",
              '-v',
              os.path.abspath(os.path.join(test_dir, ".internal", "run_student")) + ":/bin/run_student",
              '-w',
              '/task',
              args.container,
              '/bin/bash')
