# This test is made to be run on a very constrained architecture (boot2docker)
# It would be very difficult to make it run everywhere.
# If it don't work as-is on your arch, you can simply disable the TEST_DOCKER_JOB_MANAGER
# flag and trust the code, or you can modify the config in the test to make it run.

TEST_DOCKER_JOB_MANAGER = True

from backend.job_managers.remote_docker import RemoteDockerJobManager
from nose.plugins.skip import SkipTest
import docker
import os

class TestDockerJobManager(object):
    def setUp(self):
        if not TEST_DOCKER_JOB_MANAGER:
            raise SkipTest("Testing the Docker Job Manager is disabled.")

        self.docker_connection = docker.Client(base_url="tcp://192.168.59.103:2375")

        # Force the removal of all containers/images linked to this test
        try:
            self.docker_connection.remove_container("inginious-agent", force=True)
        except:
            pass

        try:
            self.docker_connection.remove_image("ingi/inginious-agent", force=True)
        except:
            pass

        self.setUpDocker()
        self.job_manager = None
        self.setUpJobManager()

    def setUpDocker(self):
        pass

    def setUpJobManager(self):
        pass

    def start_manager(self):
        self.job_manager = RemoteDockerJobManager([{
            "remote_host": "192.168.59.103",
            "remote_docker_port": 2375,
            "remote_agent_port": 63456
        }], {"default": "ingi/inginious-c-default"}, is_testing=True)

    def build_fake_agent(self, dockerfile="FakeAgentDockerfile"):
        dockerfile_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),"utils/"))
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
        #sanitize a bit Docker...
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
        assert RemoteDockerJobManager.is_agent_valid_and_started(self.docker_connection) is True


class TestDockerJobManagerAgentAlreadyStartedButDead(TestDockerJobManager):
    def setUpDocker(self):
        self.build_fake_agent("FakeAgentDockerfile")
        self.start_fake_agent()
        self.docker_connection.kill("inginious-agent")

    def test_agent_already_started_but_dead(self):
        assert RemoteDockerJobManager.is_agent_valid_and_started(self.docker_connection) is False

class TestDockerJobManagerInvalidAgentAlreadyStarted(TestDockerJobManager):
    def setUpDocker(self):
        self.build_fake_agent("FakeAgentWrongDockerfile")
        self.start_fake_agent()

    def test_invalid_agent_already_started(self):
        assert RemoteDockerJobManager.is_agent_valid_and_started(self.docker_connection) is False

class TestDockerJobManagerNoAgentStarted(TestDockerJobManager):
    def setUpDocker(self):
        pass

    def test_invalid_agent_already_started(self):
        assert RemoteDockerJobManager.is_agent_valid_and_started(self.docker_connection) is False

class TestDockerJobManagerRun(TestDockerJobManager):
    def setUpDocker(self):
        self.build_fake_agent("FakeAgentDockerfile")

    def setUpJobManager(self):
        self.start_manager()

    def test_docker_job_manager_run(self):
        assert len(self.job_manager._agents_info) == 1