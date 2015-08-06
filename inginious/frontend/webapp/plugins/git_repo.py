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
""" A plugin that allows to save submissions to a Git repository """
import Queue
import StringIO
import base64
import os.path
import shutil
import tarfile
import threading

from sh import git  # pylint: disable=no-name-in-module

import inginious.common.custom_yaml


class SubmissionGitSaver(threading.Thread):
    """
        Thread class that saves results from submission in the git repo.
        It must be a thread as a git commit can take some time and because we extract archives returned by Job Manager.
        But it must also be launched only one time as our git operations are not really process/tread-safe ;-)
    """

    def __init__(self, plugin_manager, config):
        threading.Thread.__init__(self)
        self.queue = Queue.Queue()
        mustdoinit = False
        self.repopath = config.get("repo_directory", "./repo_submissions")
        if not os.path.exists(self.repopath):
            mustdoinit = True
            os.mkdir(self.repopath)
        self.git = git.bake('--work-tree=' + self.repopath, '--git-dir=' + os.path.join(self.repopath, '.git'))
        if mustdoinit:
            self.git.init()
        plugin_manager.add_hook('submission_done', self.add)
        print "SubmissionGitSaver started"

    def add(self, submission, job):
        """ Add a new submission to the repo (add the to queue, will be saved async)"""
        self.queue.put((submission, job))

    def run(self):
        while True:
            try:
                submission, job = self.queue.get()
                self.save(submission, job)
            except Exception as inst:
                print "Exception in JobSaver: " + str(inst)

    def save(self, submission, job):
        """ saves a new submission in the repo (done async) """
        # Save submission to repo
        print "Save submission " + str(submission["_id"]) + " to git repo"
        # Verify that the directory for the course exists
        if not os.path.exists(os.path.join(self.repopath, submission["courseid"])):
            os.mkdir(os.path.join(self.repopath, submission["courseid"]))
        # Idem with the task
        if not os.path.exists(os.path.join(self.repopath, submission["courseid"], submission["taskid"])):
            os.mkdir(os.path.join(self.repopath, submission["courseid"], submission["taskid"]))
        # Idem with the username, but empty it
        dirname = os.path.join(self.repopath, submission["courseid"], submission["taskid"], submission["username"])
        if os.path.exists(dirname):
            shutil.rmtree(dirname)
        os.mkdir(dirname)
        # Now we can put the input, the output and the zip
        open(os.path.join(dirname, 'submitted_on'), "w+").write(str(submission["submitted_on"]))
        open(os.path.join(dirname, 'input.yaml'), "w+").write(inginious.common.custom_yaml.dump(submission["input"]))
        result_obj = {
            "result": job["result"],
            "text": (job["text"] if "text" in job else None),
            "problems": (job["problems"] if "problems" in job else {})
        }
        open(os.path.join(dirname, 'result.yaml'), "w+").write(inginious.common.custom_yaml.dump(result_obj))
        if "archive" in job:
            os.mkdir(os.path.join(dirname, 'output'))
            tar = tarfile.open(mode='r:gz', fileobj=StringIO.StringIO(base64.b64decode(job["archive"])))
            tar.extractall(os.path.join(dirname, 'output'))
            tar.close()

        self.git.add('--all', '.')
        title = " - ".join([str(submission["courseid"]) + "/" + str(submission["taskid"]),
                            str(submission["_id"]),
                            submission["username"],
                            ("success" if "result" in job and job["result"] == "success" else "failed")])
        self.git.commit('-m', title)


def init(plugin_manager, _, _2, config):
    """
        Init the plugin

        Available configuration:
        ::

            {
                "plugin_module": "webapp.plugins.git_repo",
                "repo_directory": "./repo_submissions"
            }

    """
    submission_git_saver = SubmissionGitSaver(plugin_manager, config)
    submission_git_saver.daemon = True
    submission_git_saver.start()
