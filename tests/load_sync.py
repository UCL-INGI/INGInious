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
import json
import threading
import time
import unittest

import webtest

from tests import *
import app_frontend
import inginious.backend
import inginious.common.base
import inginious.frontend
import inginious.frontend.session
import inginious.frontend.submission_manager
class SyncSubmitter(threading.Thread):
    """ Launch a sync submission """

    def __init__(self, queue, tid):
        threading.Thread.__init__(self)
        self.queue = queue
        self.tid = tid
    
    def assertion(self, stmtstr, stmt):
        self.queue.put((stmtstr, stmt))
    
    def run(self):
        print "\033[1;34m--> STARTING THREAD " + str(self.tid) + "\033[0m"
        t0 = time.time()
        resp = appt.post('/grader', json.dumps({"xqueue_body": json.dumps({ "student_response": "{Browse \'Hello World!\'}", "grader_payload": json.dumps({'tid':"HelloWorld"})})}))
        t1 = time.time() - t0
        self.assertion('resp.status_int == 200', resp.status_int == 200)
        print "\033[1;34m--> FINISHING THREAD " + str(self.tid) + " in " + str(t1) + "seconds\033[0m"

class Watcher(threading.Thread):
    """ Launch a sync submission """

    def __init__(self):
        threading.Thread.__init__(self)
        self.cont = True
    
    def stop(self):
        self.cont = False
    
    def run(self):
        while self.cont:
            resp = appt.get('/tests/stats')
            print "\033[1;33m--> Waiting jobs : " + resp.body +  "\033[0m"
            time.sleep(1)

class load_sync(unittest.TestCase):
    def setUp(self):
        self.jm = inginious.frontend.submission_manager.get_job_manager()
        self.queue = Queue.Queue()
        self.thqueue = Queue.Queue()
        
    def test_sync_load(self):
        '''Tests some number of task launching'''
        print "\033[1m-> load-sync: lot of sync submissions\033[0m"
        
        # Start resource watcher
        watchth = Watcher()
        watchth.start()
        
        # Launch threads
        for x in range(0, 10):
            th = SyncSubmitter(self.queue,x)
            self.thqueue.put(th)
            th.daemon = True
            th.start()
        
        # Join threads
        while not self.thqueue.empty():
            item = self.thqueue.get()
            item.join()
        
        # Stop resource watcher
        watchth.stop()
        watchth.join()
          
    def tearDown(self):
        while not self.queue.empty():
            item = self.queue.get()
            assert item[1], item[1]

if __name__ == "__main__":
    resp = appt.get('/tests/stats', status='*')
    if resp.status_int == 200:
        unittest.main()
    else:
        print "\033[31;1m-> load-sync: job manager plugin not running\033[0m"
