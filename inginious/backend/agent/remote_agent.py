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
""" Agent, managing docker (remote version) """

import copy
import os.path
from shutil import rmtree
import tarfile
import tempfile
import threading

import rpyc
from rpyc.utils.server import ThreadedServer

import inginious.common.base
from inginious.backend.agent.simple_agent import SimpleAgent


class RemoteAgent(SimpleAgent):
    """
        An agent that can be called remotely via RPyC.
        It can handle multiple requests at a time, but RPyC calls have to be made using the ```async``` function.
    """

    def __init__(self, port, task_directory, course_factory, task_factory, ssh_manager_port=None, tmp_dir="./agent_tmp", sync_enabled=True):
        SimpleAgent.__init__(self, task_directory, course_factory, task_factory, ssh_manager_port, tmp_dir)
        self.sync_enabled = sync_enabled
        self.logger.debug("Starting RPyC server - inginious.backend connection")
        self._backend_server = ThreadedServer(self._get_agent_backend_service(), port=port,
                                              protocol_config={"allow_public_attrs": True, 'allow_pickle': True})
        self._backend_server.start()

    def _update_image_aliases(self, image_aliases):
        """ Updates the image aliases list """
        self.image_aliases = image_aliases

    def _get_agent_backend_service(self):
        """ Returns a RPyC service associated with this Agent """
        handle_batch_job = self.handle_batch_job
        handle_get_batch_container_metadata = self.handle_get_batch_container_metadata
        handle_job = self.handle_job
        update_image_aliases = self._update_image_aliases
        sync_enabled = self.sync_enabled
        task_directory = self.task_directory
        logger = self.logger

        class AgentService(rpyc.Service):
            def __init__(self, conn):
                logger.info("Backend connected")
                rpyc.Service.__init__(self, conn)

            def exposed_update_image_aliases(self, image_aliases):
                """ Updates the image aliases """
                logger.info("Updating image aliases...")
                update_image_aliases(copy.deepcopy(image_aliases))

            def exposed_new_batch_job(self, job_id, container_name, input_data, callback):
                """ Creates, executes and returns the results of a batch job.
                    The return value of a batch job is always a compressed(gz) tar file.
                :param job_id: The distant job id
                :param container_name: The container image to launch
                :param input_data: Input (.tgz file) as made in remote_manual_agent
                :return: a dict, containing either:
                    - {"retval":0, "stdout": "...", "stderr":"...", "file":"..."}
                        if everything went well. (where file is a tgz file containing the content of the /output folder from the container)
                    - {"retval":"...", "stdout": "...", "stderr":"..."}
                        if the container crashed (retval is an int != 0) (can also contain file, but not mandatory)
                    - {"retval":-1, "stderr": "the error message"}
                        if the container failed to start
                """

                # Copy the remote tar archive locally
                tmpfile = tempfile.TemporaryFile()
                tmpfile.write(input_data.read())
                tmpfile.seek(0)

                # Unarchive input_data
                batch_args = handle_get_batch_container_metadata(container_name)[2]
                input_data = {}
                tar = tarfile.open(fileobj=tmpfile, mode='r:gz')
                for n in tar.getnames():
                    if n in batch_args and batch_args[n]["type"] == "file":
                        input_data[n] = tar.extractfile(n)
                    elif n in batch_args and batch_args[n]["type"] == "text":
                        input_data[n] = tar.extractfile(n).read()
                    else:
                        logger.warning("Unknown key %s for batch container %s!", n, container_name)

                def _threaded_execute():
                    try:
                        retval = handle_batch_job(job_id, container_name, input_data)
                        callback(retval)
                    except Exception as e:
                        callback({"retval": -1, "stderr": str(e)})

                threading.Thread(target=_threaded_execute).start()

            def exposed_get_batch_container_metadata(self, container_name):
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
                return handle_get_batch_container_metadata(container_name)

            def exposed_new_job(self, job_id, course_id, task_id, inputdata, debug, ssh_callback, callback_return):
                """ Creates, executes and returns the results of a new job (in a separate thread, distant version)
                :param job_id: The distant job id
                :param course_id: The course id of the linked task
                :param task_id: The task id of the linked task
                :param inputdata: Input data, given by the student (dict)
                :param debug: Can be False (normal mode), True (outputs more data), or "ssh" (starts an ssh server in the container)
                :param ssh_callback: ssh callback function. Takes two parameters: (conn_id, private_key). Is only called if debug == "ssh".
                :param callback_return: The callback on the remote server that will be called with the return value
                """

                # Deepcopy inputdata (to bypass "passage by reference" of RPyC)
                inputdata = copy.deepcopy(inputdata)

                def _threaded_execute():
                    try:
                        retval = handle_job(job_id, course_id, task_id, inputdata, debug, ssh_callback)
                        callback_return(retval)
                    except Exception as e:
                        callback_return({"result": "crash", "text": "An error occured in the Agent: {}".format(str(e))})

                threading.Thread(target=_threaded_execute).start()

            def exposed_get_task_directory_hashes(self):
                """ Get the list of files from the local task directory
                :return: a dict in the form {path: (hash of the file, stat of the file)} containing all the files
                         from the local task directory, with their hash, or None if sync is disabled.
                """
                if sync_enabled:
                    logger.info("Getting the list of files from the local task directory for the inginious.backend.")
                    return inginious.common.base.directory_content_with_hash(task_directory)
                else:
                    logger.info("Warning the inginious.backend that sync is disabled.")
                    return None

            def exposed_update_task_directory(self, remote_tar_file, to_delete):
                """ Updates the local task directory
                :param tarfile: a compressed tar file that contains files that needs to be updated on this agent
                :param to_delete: a list of path to file to delete on this agent
                """
                if sync_enabled:
                    logger.info("Updating task directory...")
                    # Copy the remote tar archive locally
                    tmpfile = tempfile.TemporaryFile()
                    tmpfile.write(remote_tar_file.read())
                    tmpfile.seek(0)
                    tar = tarfile.open(fileobj=tmpfile, mode='r:gz')

                    # Verify security of the tar archive
                    bd = os.path.abspath(task_directory)
                    for n in tar.getnames():
                        if not os.path.abspath(os.path.join(bd, n)).startswith(bd):
                            logger.error("Tar file given by the inginious.backend is invalid!")
                            return


                    # Verify security of the list of file to delete
                    for n in to_delete:
                        if not os.path.abspath(os.path.join(bd, n)).startswith(bd):
                            logger.error("Delete file list given by the inginious.backend is invalid!")
                            return

                    # Extract the tar file
                    tar.extractall(task_directory)
                    tar.close()
                    tmpfile.close()

                    # Delete unneeded files
                    for n in to_delete:
                        c_path = os.path.join(task_directory, n)
                        if os.path.exists(c_path):
                            if os.path.isdir(c_path):
                                rmtree(c_path)
                            else:
                                os.unlink(c_path)

                    logger.info("Task directory updated")
                else:
                    logger.warning("Backend tried to sync tasks files while sync is disabled!")

        return AgentService
