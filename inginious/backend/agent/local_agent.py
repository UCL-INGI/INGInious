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
""" Agent, managing docker (local version) """

import threading

from inginious.backend.agent.simple_agent import SimpleAgent


class LocalAgent(SimpleAgent):
    """ An agent made to be run locally (launched directly by the backend). It can handle multiple requests at a time. """

    def __init__(self, image_aliases, task_directory, course_factory, task_factory, tmp_dir="./agent_tmp"):
        SimpleAgent.__init__(self, task_directory, course_factory, task_factory, tmp_dir)
        self.image_aliases = image_aliases

    def new_job(self, job_id, course_id, task_id, inputdata, debug, callback_status, final_callback):
        """ Creates, executes and returns the results of a new job (in a separate thread)
        :param job_id: The distant job id
        :param course_id: The course id of the linked task
        :param task_id: The task id of the linked task
        :param inputdata: Input data, given by the student (dict)
        :param debug: A boolean, indicating if the job should be run in debug mode or not
        :param callback_status: Not used, should be None.
        :param final_callback: Callback function called when the job is done; one argument: the result.
        """

        t = threading.Thread(target=lambda: self._handle_job_threaded(job_id, course_id, task_id, inputdata, debug, callback_status, final_callback))
        t.daemon = True
        t.start()

    def new_batch_job(self, job_id, container_name, input_data, callback):
        """ Creates, executes and returns the results of a batch container.
            The return value of a batch container is always a compressed(gz) tar file.
        :param job_id: The distant job id
        :param container_name: The container image to launch
        :param input_data: inputdata is a dict containing all the keys of get_batch_container_metadata(container_name)[2].
            The values associated are file-like objects for "file" types and  strings for "text" types.
        :param callback: the callback that will be called when the batch job is done
        """
        t = threading.Thread(target=lambda: self._handle_batch_job_threaded(job_id, container_name, input_data, callback))
        t.daemon = True
        t.start()

    def get_batch_container_metadata(self, container_name):
        """
            Returns the arguments needed by a particular batch container.
            :returns: a tuple, in the form
                ("container title",
                 "container description in restructuredtext",
                 {"key":
                    {
                     "type:" "file", #or "text",
                     "path": "path/to/file/inside/input/dir", #not mandatory in file, by default "key"
                     "name": "name of the field", #not mandatory in file, default "key"
                     "description": "a short description of what this field is used for" #not mandatory, default ""
                    }
                 }
                )
        """
        return self.handle_get_batch_container_metadata(container_name)

    def _handle_job_threaded(self, job_id, course_id, task_id, inputdata, debug, callback_status, final_callback):
        try:
            result = self.handle_job(job_id, course_id, task_id, inputdata, debug, callback_status)
            final_callback(result)
        except:
            final_callback({"result": "crash"})

    def _handle_batch_job_threaded(self, job_id, container_name, input_data, callback):
        try:
            result = self.handle_batch_job(job_id, container_name, input_data)
            callback(result)
        except:
            callback({"retval": -1, "stderr": "Unknown error"})
