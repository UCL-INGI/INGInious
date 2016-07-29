# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" A synchronized "layer" for JobManager """
import threading


class JobManagerSync(object):
    """ Runs job synchronously """

    def __init__(self, job_manager):
        self._job_manager = job_manager

    def new_job(self, task, inputdata, launcher_name="Unknown", debug=False):
        """
            Runs a new job.
            It works exactly like the JobManager class, instead that there is no callback and directly returns result.
        """
        job_semaphore = threading.Semaphore(0)

        def manage_output(job):
            """ Manages the output of this job """
            manage_output.job_return = job
            job_semaphore.release()

        self._job_manager.new_job(task, inputdata, manage_output, launcher_name, debug)
        job_semaphore.acquire()
        job_return = manage_output.job_return
        return job_return
