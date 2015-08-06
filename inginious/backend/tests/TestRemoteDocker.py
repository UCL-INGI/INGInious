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

# This test is made to be run on a very constrained architecture (boot2docker)
# It would be very difficult to make it run everywhere.
# If it don't work as-is on your arch, you can simply disable the TEST_DOCKER_JOB_MANAGER
# flag and trust the code, or you can modify the config in the test to make it run.

import os

from nose.plugins.skip import SkipTest
import docker

from inginious.backend.job_managers.remote_docker import RemoteDockerJobManager
from inginious.common.course_factory import create_factories

TEST_ENV = os.environ.get("TEST_ENV", None)


class TestDockerJobManager(object):
    def setUp(self):

        if TEST_ENV is None:
            raise SkipTest("Testing the Docker Job Manager is disabled.")
        elif TEST_ENV in ["boot2docker", "boot2docker-local"]:
            self.docker_connection = docker.Client(base_url="tcp://192.168.59.103:2375")
        elif TEST_ENV == "travis":
            self.docker_connection = docker.Client(base_url="tcp://localhost:2375")
        else:
            raise Exception("Unknown method for testing the Docker Job Manager!")

        # Force the removal of all containers/images linked to this test
        try:
            self.docker_connection.remove_container("inginious-agent", force=True)
        except:
            pass

        try:
            self.docker_connection.remove_image("ingi/inginious-agent", force=True)
        except:
            pass

        self.course_factory, self.task_factory = create_factories("./tasks")

        self.setUpDocker()
        self.job_manager = None
        self.setUpJobManager()

    def setUpDocker(self):
        pass

    def setUpJobManager(self):
        pass

    def start_manager(self):
        if TEST_ENV in ["boot2docker", "boot2docker-local"]:
            self.job_manager = RemoteDockerJobManager([{
                "remote_host": "192.168.59.103",
                "remote_docker_port": 2375,
                "remote_agent_port": 63456
            }], {"default": "ingi/inginious-c-default"}, "./tasks", self.course_factory, self.task_factory, is_testing=True)
        elif TEST_ENV == "travis":
            self.job_manager = RemoteDockerJobManager([{
                "remote_host": "localhost",
                "remote_docker_port": 2375,
                "remote_agent_port": 63456
            }], {"default": "ingi/inginious-c-default"}, "./tasks", self.course_factory, self.task_factory, is_testing=True)
        self.job_manager.start()

    def build_fake_agent(self, dockerfile="FakeAgentDockerfile"):
        dockerfile_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "utils/"))
        print [line for line in self.docker_connection.build(dockerfile_dir, dockerfile=dockerfile, rm=True, tag="ingi/inginious-agent")]

    def start_fake_agent(self):
        response = self.docker_connection.create_container(
            "ingi/inginious-agent",
            detach=True,
            name="inginious-agent"
        )
        container_id = response["Id"]

        # Start the container
        self.docker_connection.start(container_id)

    def tearDown(self):
        # sanitize a bit Docker...
        if self.job_manager is not None:
            self.job_manager.close()

        try:
            self.docker_connection.remove_container("inginious-agent", force=True)
        except:
            pass

        try:
            self.docker_connection.remove_image("ingi/inginious-agent", force=True)
        except:
            pass


class TestDockerJobManagerNoUpdateNeeded(TestDockerJobManager):
    def setUpDocker(self):
        self.build_fake_agent("FakeAgentDockerfile")

    def test_agent_no_update_needed(self):
        assert RemoteDockerJobManager.is_agent_image_update_needed(self.docker_connection) is False


class TestDockerJobManagerUpdateNeeded(TestDockerJobManager):
    def setUpDocker(self):
        self.build_fake_agent("FakeAgentWrongDockerfile")

    def test_agent_update_needed(self):
        assert RemoteDockerJobManager.is_agent_image_update_needed(self.docker_connection) is True


class TestDockerJobManagerNoImage(TestDockerJobManager):
    def setUpDocker(self):
        pass

    def test_agent_no_image(self):
        assert RemoteDockerJobManager.is_agent_image_update_needed(self.docker_connection) is True


class TestDockerJobManagerAgentAlreadyStarted(TestDockerJobManager):
    def setUpDocker(self):
        self.build_fake_agent("FakeAgentDockerfile")
        self.start_fake_agent()

    def test_agent_already_started(self):
        assert RemoteDockerJobManager.is_agent_valid_and_started(self.docker_connection, "inginious-agent") is True


class TestDockerJobManagerAgentAlreadyStartedButDead(TestDockerJobManager):
    def setUpDocker(self):
        self.build_fake_agent("FakeAgentDockerfile")
        self.start_fake_agent()
        self.docker_connection.kill("inginious-agent")

    def test_agent_already_started_but_dead(self):
        assert RemoteDockerJobManager.is_agent_valid_and_started(self.docker_connection, "inginious-agent") is False


class TestDockerJobManagerInvalidAgentAlreadyStarted(TestDockerJobManager):
    def setUpDocker(self):
        self.build_fake_agent("FakeAgentWrongDockerfile")
        self.start_fake_agent()

    def test_invalid_agent_already_started(self):
        assert RemoteDockerJobManager.is_agent_valid_and_started(self.docker_connection, "inginious-agent") is False


class TestDockerJobManagerNoAgentStarted(TestDockerJobManager):
    def setUpDocker(self):
        pass

    def test_invalid_agent_already_started(self):
        assert RemoteDockerJobManager.is_agent_valid_and_started(self.docker_connection, "inginious-agent") is False


class TestDockerJobManagerRun(TestDockerJobManager):
    def setUpDocker(self):
        self.build_fake_agent("FakeAgentDockerfile")

    def setUpJobManager(self):
        self.start_manager()

    def test_docker_job_manager_run(self):
        assert len(self.job_manager._agents_info) == 1
