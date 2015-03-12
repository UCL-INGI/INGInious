# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
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
import Queue
import time
import unittest
import uuid

from inginious.backend.job_manager import JobManager
from inginious.common.base import INGIniousConfiguration
from tests import *
import inginious.backend._submitter
import inginious.common.base
import inginious.common.courses
import inginious.common.tasks
import inginious.frontend
import inginious.frontend.submission_manager
class backend_jobs(unittest.TestCase):
    def setUp(self):
        self.jm = inginious.frontend.submission_manager.get_job_manager()
    
    def job_finished(self, jid, task, final_dict):
        '''Catches ending of a test job and tests the final state of the queue'''
        self.done = True
        
        # Check if received job matches and if state in the queue is not running
        assert self.jid == jid
        
        # Check content of the result
        assert final_dict['result'] == "success"
    
    def test_job_manager(self):
        '''Tests if a job adds in the queue and is treated correctly'''
        print "\033[1m-> inginious.backend-jobs: job manager\033[0m"
        self.done = False
        t = inginious.common.tasks.Task(inginious.common.courses.Course('test'), 'task1')
        self.jid = self.jm.new_job(t, {"input":{"unittest/decimal":"12.5"}, "limits":t.get_limits()}, self.job_finished)
        assert isinstance(self.jid, uuid.UUID)
        
        while not self.done:
            time.sleep(1)
            print "Waiting for the job to end..."
        
        print "Job finished"
        
    def tearDown(self):
        pass

if __name__ == "__main__":
    if not inginious.common.base.INGIniousConfiguration.get('tests',{}).get('host_url', ''):
        unittest.main()
    else:
        print "\033[31;1m-> inginious.backend-jobs: tests cannot be run remotely\033[0m"
