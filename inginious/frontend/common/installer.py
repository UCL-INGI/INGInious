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
""" Shared methods for the command line tool that installs the frontends """
import abc

import os
import socket
import uuid
import docker
from docker.utils import kwargs_from_env
import sys
from gridfs import GridFS
import rpyc
from pymongo import MongoClient
import time
import shutil
import inginious.common.custom_yaml as yaml

HEADER = '\033[95m'
INFO = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[33m'
WHITE = '\033[97m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
DOC = '\033[39m'
BACKGROUND_RED = '\033[101m'

class Installer(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config_path = None):
        self._config_path = config_path

    #######################################
    #          Display functions          #
    #######################################

    def _display_header(self, title):
        """ Displays an header in the console """
        print ""
        print BOLD + HEADER + "--- " + title + " ---" + ENDC

    def _display_warning(self, content):
        """ Displays a warning in the console """
        print WARNING + "(WARN) " + content + ENDC

    def _display_info(self, content):
        """ Displays an info message in the console """
        print INFO + "(INFO) " + content + ENDC

    def _display_question(self, content):
        """ Displays a preamble to a question """
        print DOC + content + ENDC

    def _display_error(self, content):
        """ Displays an error """
        print WHITE + BACKGROUND_RED + "(ERROR) " + content + ENDC

    def _display_big_warning(self, content):
        """ Displays a BIG warning """
        print ""
        print BOLD + WARNING + "--- WARNING ---" + ENDC
        print WARNING + content + ENDC
        print ""

    def _ask_with_default(self, question, default):
        default = str(default)
        answer = raw_input(DOC + UNDERLINE + question + " [" + default + "]:" + ENDC + " ")
        if answer == "":
            answer = default
        return answer

    def _ask_boolean(self, question, default):
        while True:
            val = self._ask_with_default(question, ("yes" if default else "no")).lower()
            if val in ["yes", "y", "1", "true", "t"]:
                return True
            elif val in ["no", "n", "0", "false", "f"]:
                return False
            self._display_question("Please answer 'yes' or 'no'.")

    #######################################
    #            Main function            #
    #######################################

    def run(self):
        """ Run the installator """
        self._display_header("DOCKER CONFIGURATION")
        def_backend, def_remote_host, def_remote_docker_port, def_use_tls = self.generate_docker_default()
        options = {}
        while True:
            options = {}
            backend = self.ask_docker_backend(def_backend)
            if backend == "remote":
                self._display_info("Backend chosen: remote. Let's configure the agents.")
                options = self.configure_backend_remote(def_remote_host, def_remote_docker_port, def_use_tls)
                if options is not None:
                    break
            elif backend == "local":
                self._display_info("Backend chosen: local. Testing the configuration.")
                options = {"backend": "local"}
                if not self.test_basic_docker_conf("local"):
                    self._display_error("An error occured while testing the configuration.")
                    if self._ask_boolean("Would you like to continue anyway?", False):
                        break
                else:
                    break
            else:
                self._display_warning("Backend chosen: remote_manual. As it is a really advanced feature, you will have to configure it yourself in "
                                   "the configuration file, at the end of the setup process.")
                options = {"backend": "remote_manual"}
                break

        self._display_header("MONGODB CONFIGURATION")
        mongo_opt = self.configure_mongodb()
        options.update(mongo_opt)

        self._display_header("TASK DIRECTORY")
        task_directory_opt = self.configure_task_directory()
        options.update(task_directory_opt)

        self._display_header("CONTAINERS")
        containers_opt = self.configure_containers(options)
        options.update(containers_opt)

        self._display_header("MISC")
        misc_opt = self.configure_misc()
        options.update(misc_opt)

        options = self.frontend_specific_configuration(options)

        self._display_header("END")
        file_dir = self._config_path or os.path.join(os.getcwd(), self.configuration_filename())
        try:
            yaml.dump(options, open(file_dir, "w"))
            self._display_info("Successfully written the configuration file")
        except:
            self._display_error("Cannot write the configuration file on disk. Here is the content of the file")
            print yaml.dump(options)

    @abc.abstractmethod
    def frontend_specific_configuration(self, options):
        """ Modify the options for a specific frontend. Should return the new option dict """
        return options

    @abc.abstractmethod
    def configuration_filename(self):
        """ Returns the name of the configuration file """
        return "configuration.yaml"

    @abc.abstractmethod
    def support_remote_debugging(self):
        """ Returns True if the frontend supports remote debugging, False else"""
        return False

    #######################################
    #       Docker configuration          #
    #######################################

    def generate_docker_default(self):
        """ Generates "default" configuration for Docker and tests it """
        docker_args = kwargs_from_env()

        backend = None
        remote_host = None
        remote_docker_port = 2375
        use_tls = False

        if docker_args == {}:
            docker_args["base_url"] = "unix:///var/run/docker.sock"

        if "base_url" in docker_args:
            self._display_info("Found docker base_url")
            try:
                if docker_args["base_url"].startswith("tcp://") or \
                        docker_args["base_url"].startswith("http://") or \
                        docker_args["base_url"].startswith("https://"):
                    backend = "remote"
                    info = docker_args["base_url"].split("://")
                    host_info = info[1].split(':')
                    remote_host = host_info[0]
                    if len(remote_host) > 1:
                        remote_docker_port = int(host_info[1])
                    if info[0] == "https":
                        use_tls = True
                    if "tls" in docker_args:
                        try:
                            use_tls = os.path.dirname(docker_args["tls"].verify)
                        except:
                            self._display_warning("Unable to parse the TLS configuration")
                    self._display_info("Current Docker configuration suggest the use of the remote backend")
                    self._display_info("Found Docker host: %s" % remote_host)
                    self._display_info("Found Docker port: %s" % remote_docker_port)
                    self._display_info("TLS cert dirt: %s" % use_tls)
                elif docker_args["base_url"].startswith("unix://"):
                    backend = "local"
                    self._display_info("Current Docker configuration suggest the use of the local backend")
                else:
                    self._display_warning("Unable to read docker base_url: %s" % docker_args["base_url"])
            except:
                self._display_warning("Unable to read docker base_url")

        if backend is not None:
            self._display_info("Testing the default configuration")
            if self.test_basic_docker_conf(backend, remote_host, remote_docker_port, use_tls):
                self._display_info("Default configuration works")
            else:
                self._display_info("Default configuration not working")
                backend = None
                remote_host = None
                remote_docker_port = 2375
                use_tls = False

        if backend is None:
            self._display_big_warning("We are unable to find a running Docker instance. You can either continue to run the tool and complete "
                                      "everything manually, or exit it and try to make the 'docker info' command work.")

        if backend == "local" and (sys.platform.startswith("darwin") or sys.platform.startswith("win")):
            self._display_big_warning("As you are on OS X or on Windows, and that your Docker client is configured to be local, there is probably a "
                                      "problem with your configuration. You can either continue to run the tool and complete everything manually, "
                                      "or exit it and try to make the 'docker info' command work.")
            backend = "remote"

        return backend, remote_host, remote_docker_port, use_tls

    def test_basic_docker_conf(self, backend, remote_host=None, remote_docker_port=None, use_tls=None):
        """ Test if the configuration given for connecting to Docker works"""
        try:
            if backend == "remote":
                if isinstance(use_tls, basestring):
                    tls_config = docker.tls.TLSConfig(
                        client_cert=(use_tls + '/cert.pem', use_tls + '/key.pem'),
                        verify=use_tls + '/ca.pem'
                    )
                    protocol = "https"
                elif use_tls is True:
                    tls_config = True
                    protocol = "https"
                else:
                    tls_config = False
                    protocol = "http"
                docker_connection = docker.Client(base_url=protocol+"://" + remote_host + ":" + str(remote_docker_port), tls=tls_config)
            elif backend == "local":
                docker_connection = docker.Client(**kwargs_from_env())
            else:
                self._display_warning("- The setup tool does not support remote manual agents. The configuration will not be checked.")
                return True
        except Exception as e:
            self._display_error("- Unable to connect to Docker. Error was %s" % str(e))
            return False

        try:
            self._display_info("- Asking Docker some info")
            if docker.utils.compare_version('1.19', docker_connection.version()['ApiVersion']) < 0:
                self._display_error("- Docker version >= 1.7.0 is required.")
                return False
        except Exception as e:
            self._display_error("- Unable to contact Docker. Error was %s" % str(e))
            return False
        self._display_info("- Successfully got info from Docker. Docker connection works.")

        if backend == "local":
            self._display_info("- Verifying access to cgroups")
            try:
                from cgutils import cgroup
            except:
                self._display_error("- Cannot import cgroup-utils. Is the package installed?")
                return False
            try:
                cgroup.scan_cgroups("memory")
            except:
                self._display_error("- Cannot find cgroup. Are you sure the Docker instance is local?")
                return False

        return True

    def get_agent_environment(self, agent_name, agent_port, agent_ssh_port, remote_host, remote_docker_port, use_tls, local_location,
                              cgroups_location):
        """ Get the environment for the agent. Returns None if an error happens. """
        try:
            if isinstance(use_tls, basestring):
                tls_config = docker.tls.TLSConfig(
                    client_cert=(use_tls + '/cert.pem', use_tls + '/key.pem'),
                    verify=use_tls + '/ca.pem'
                )
                protocol = "https"
            elif use_tls is True:
                tls_config = True
                protocol = "https"
            else:
                tls_config = False
                protocol = "http"
            docker_connection = docker.Client(base_url=protocol + "://" + remote_host + ":" + str(remote_docker_port), tls=tls_config)
        except Exception as e:
            self._display_error("- Cannot connect to the remote Docker instance: %s" % str(e))
            return None

        environment = {"AGENT_CONTAINER_NAME": agent_name, "AGENT_PORT": agent_port, "AGENT_SSH_PORT": (agent_ssh_port or "")}
        volumes = {'/sys/fs/cgroup/': {}}
        binds = {cgroups_location: {'ro': False, 'bind': "/sys/fs/cgroup"}}

        if local_location.startswith("unix://"):
            volumes['/var/run/docker.sock'] = {}
            binds[local_location[7:]] = {'ro': False, 'bind': '/var/run/docker.sock'}
            environment["DOCKER_HOST"] = "unix:///var/run/docker.sock"
        elif local_location.startswith("tcp://"):
            environment["DOCKER_HOST"] = local_location
            if use_tls:
                environment["DOCKER_TLS_VERIFY"] = "on"
        else:
            self._display_error("- Unknown protocol for Docker local location: %s" % local_location)
            return None

        return docker_connection, environment, volumes, binds

    def test_agent_pull(self, agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port, use_tls, local_location, cgroups_location):
        """ Pull the agent to do remote tests """
        data = self.get_agent_environment(agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port, use_tls, local_location,
                                          cgroups_location)
        if data is None:
            return False
        docker_connection, environment, volumes, binds = data

        try:
            docker_connection.pull("ingi/inginious-agent:latest")
            docker_connection.inspect_image("ingi/inginious-agent")
            return True
        except:
            return False

    def run_remote_container(self, agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port, use_tls, local_location,
                             cgroups_location, command):
        """ Run a remote Docker container and get its output. Returns None in case of error """
        data = self.get_agent_environment(agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port, use_tls, local_location,
                                          cgroups_location)
        if data is None:
            return None
        docker_connection, environment, volumes, binds = data

        try:
            response = docker_connection.create_container(
                "ingi/inginious-agent",
                environment=environment,
                detach=True,
                name=agent_id,
                volumes=volumes,
                command=command
            )
            container_id = response["Id"]
        except Exception as e:
            self._display_error("- Cannot create container: %s" % str(e))
            return None

        try:
            # Start the container
            docker_connection.start(container_id, network_mode="host", binds=binds)
        except Exception as e:
            self._display_error("- Cannot start container: %s" % str(e))
            try:
                docker_connection.remove_container(container_id)
            except:
                pass
            return None

        try:
            docker_connection.wait(container_id, timeout=20)
            stdout = str(docker_connection.logs(container_id, stdout=True, stderr=False))
        except Exception as e:
            self._display_error("- Cannot retrieve output of container: %s" % str(e))
            try:
                docker_connection.remove_container(container_id)
            except:
                pass
            return None

        try:
            docker_connection.remove_container(container_id)
        except:
            pass

        return stdout

    def test_agent_docker_location(self, agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port, use_tls, local_location,
                                   cgroups_location):
        """ Test local docker location """
        stdout = self.run_remote_container(agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port, use_tls, local_location,
                                           cgroups_location, ["docker", "info"])
        return stdout is not None and "Execution Driver:" in stdout

    def test_agent_docker_cgroup(self, agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port,
                                 use_tls, local_location, cgroups_location):
        """ Test cgroup location on the agent's host """
        stdout = self.run_remote_container(agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port, use_tls, local_location,
                                           cgroups_location, ["ls", "/sys/fs/cgroup"])
        return stdout is not None and "cpuacct" in stdout

    def start_agent_container(self, agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port, use_tls, local_location, cgroups_location):
        """ Starts a remote agent container """
        data = self.get_agent_environment(agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port, use_tls, local_location,
                                          cgroups_location)
        if data is None:
            return None, None
        docker_connection, environment, volumes, binds = data

        try:
            response = docker_connection.create_container(
                "ingi/inginious-agent",
                environment=environment,
                detach=True,
                name=agent_id,
                volumes=volumes
            )
            container_id = response["Id"]
        except Exception as e:
            self._display_error("- Cannot create container: %s" % str(e))
            return docker_connection, None

        try:
            # Start the container
            docker_connection.start(container_id, network_mode="host", binds=binds)
        except Exception as e:
            self._display_error("- Cannot start container: %s" % str(e))
            try:
                docker_connection.remove_container(container_id)
            except:
                pass
            return docker_connection, None

        time.sleep(5)

        return docker_connection, container_id

    def stop_agent_container(self, docker_connection, container_id):
        """ Closes a remote agent container """
        try:
            docker_connection.remove_container(container_id, force=True)
        except:
            pass

    def test_agent_port(self, agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port, use_tls, local_location, cgroups_location):
        """ Test agent port """
        docker_connection, container_id = self.start_agent_container(agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port,
                                                                     use_tls, local_location, cgroups_location)
        if container_id is None:
            return False

        ok = False
        for i in range(0, 5): #retry five times
            try:
                conn = rpyc.connect(remote_host, agent_port, config={"allow_public_attrs": True, 'allow_pickle': True})

                # Try to access conn.root. This raises an exception when the remote RPyC is not yet fully initialized
                if not conn.root:
                    raise Exception("Cannot get remote service")
                ok = True
                break
            except:
                time.sleep(1)

        self.stop_agent_container(docker_connection, container_id)
        return ok


    def test_agent_ssh_port(self, agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port, use_tls, local_location, cgroups_location):
        """ Test agent port """
        docker_connection, container_id = self.start_agent_container(agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port,
                                                                     use_tls, local_location, cgroups_location)
        if container_id is None:
            return False

        ok = False
        for i in range(0, 5):  # retry five times
            try:
                client = socket.create_connection((remote_host, agent_ssh_port))
                client.send("something" + "\n")
                retval = ""
                while retval not in ["ok\n", "ko\n"]:
                    retval += client.recv(3)
                retval = retval.strip()
                if retval == "ko":
                    ok = True
                    break
            except:
                time.sleep(1)

        self.stop_agent_container(docker_connection, container_id)
        return ok

    def ask_docker_backend(self, default_backend=None):
        """ Ask the user to choose the backend """
        self._display_question("Please indicate which backend you would like to use. You can choose between: ")
        self._display_question("- 'local' (best choice on Linux, with Docker on the same machine);")
        self._display_question("- 'remote' (for more advanced users or users using OS X or Windows with Boot2Docker);")
        self._display_question("- 'remote_manual' (advanced users only. not help will be provided by the tool).")
        backend = self._ask_with_default("Choose a backend", default_backend)
        if backend in ["local", "remote", "remote_manual"]:
            return backend
        else:
            self._display_question("Invalid choice %s. Please retry." % backend)
            self.ask_docker_backend(default_backend)

    def configure_backend_remote(self, def_remote_host, def_remote_docker_port, def_use_tls):
        """ Configures the remote backend """
        options = {"backend": "remote", "docker_daemons": []}
        while True:
            agent_id = "inginious-agent-"+str(uuid.uuid1())
            agent = self.configure_backend_remote_agent(def_remote_host, def_remote_docker_port, def_use_tls, agent_id)
            if agent is None and len(options["docker_daemons"]) == 0:
                self._display_warning("You have not configured any agent. You will have to define one manually in the configuration.")
                if self._ask_boolean("Are you sure you do not want to retry?", False):
                    break
            elif agent is None:
                break
            else:
                options["docker_daemons"].append(agent)
                if not self._ask_boolean("Do you want to define another agent? Do this only if you have another server with a Docker instance "
                                      "available", False):
                    break
        return options

    def configure_backend_remote_agent(self, def_remote_host, def_remote_docker_port, def_use_tls, def_agent_id):
        """ Configure an agent """

        # Basic questions
        self._display_question("")
        self._display_question("Configuring an agent. Type -1 in the first field to skip this step.")
        remote_host = self._ask_with_default("Remote Docker host", def_remote_host)
        if remote_host == "-1":
            return None
        remote_docker_port = self._ask_with_default("Remote Docker port", def_remote_docker_port)
        self._display_question(" Do you use TLS? By default, it is activated on Boot2Docker. You may want:")
        self._display_question("- to enable TLS verification: simply type 'true'")
        self._display_question("- to disable TLS verification: type 'false'")
        self._display_question("- to define a custom cert: type the absolute path to the directory containing the certs")
        use_tls = self._ask_with_default("Use TLS", def_use_tls)
        if use_tls == "True" or use_tls == "true":
            use_tls = True
        if use_tls == "False" or use_tls == "false":
            use_tls = False

        # Test this basic configuration
        self._display_info("Testing connection to Docker")
        if not self.test_basic_docker_conf("remote", remote_host, remote_docker_port, use_tls):
            self._display_error("Cannot connect to Docker.")
            if self._ask_with_default("Would you like to retry?", True):
                return self.configure_backend_remote_agent(def_remote_host, def_remote_docker_port, def_use_tls, def_agent_id)
            else:
                return None

        # Ask for more specific infos
        agent_id = self._ask_with_default("Agent ID (you can leave this field blank)", def_agent_id)
        self._display_question("Please indicate the port on which the agent will bind. This port should be accessible from the current machine.")
        agent_port = self._ask_with_default("Agent port", "63456")
        agent_ssh_port = None
        if self.support_remote_debugging():
            self._display_question("If you want to enable remote debugging, please indicate another port on which the agent will bind. "
                                   "This port should be accessible from the current machine. Leave empty if you do not want to allow remote "
                                   "debugging.")
            agent_ssh_port = self._ask_with_default("Remote debugging port", "")
            if agent_ssh_port == "":
                agent_ssh_port = None

        # Try default configuration first
        local_location = "unix:///var/run/docker.sock"
        cgroups_location = "/sys/fs/cgroup"

        # Pull the inginious-agent image
        self._display_info("- Pulling the inginious-agent image. This can take time.")
        if not self.test_agent_pull(agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port, use_tls, local_location, cgroups_location):
            self._display_error("- An error occured while pulling ingi/inginious-agent")
            if self._ask_with_default("Would you like to retry?", True):
                return self.configure_backend_remote_agent(def_remote_host, def_remote_docker_port, def_use_tls, def_agent_id)
            else:
                return None

        # Test the docker local location
        self._display_info("- Guessing the agent local Docker location. This can take some time.")
        if not self.test_agent_docker_location(agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port,
                                               use_tls, local_location, cgroups_location):
            self._display_info("- Cannot guess the default local Docker location for the agent.")
            local_location_valid = False
        else:
            self._display_info("- Correctly guessed the default local Docker location for the agent.")
            local_location_valid = True

        # Test the cgroup location
        self._display_info("- Guessing the cgroup location on the agent's host. This can take some time.")
        if not self.test_agent_docker_cgroup(agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port,
                                             use_tls, local_location, cgroups_location):
            self._display_info("- Cannot guess the cgroup location on the agent's host.")
            cgroups_location_valid = False
        else:
            self._display_info("- Correctly guessed the cgroup location on the agent's host.")
            cgroups_location_valid = True

        # If we correctly guessed, ask if we should still ask the parameters
        should_ask = not cgroups_location_valid or not local_location_valid
        if not should_ask:
            should_ask = self._ask_boolean("The tool correctly guessed the configuration for cgroup and for the Docker local location. Do you "
                                           "want to change it anyway?", False)

        # Ask the parameters if needed
        while should_ask:
            cgroups_location = self._ask_with_default("cgroup location on the remote host", cgroups_location)
            local_location = self._ask_with_default("Docker location on the remote host", local_location)

            self._display_info("- Verifying the configuration. This can take time.")
            should_ask = False

            if not self.test_agent_docker_location(agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port,
                                                   use_tls, local_location, cgroups_location):
                self._display_warning("- Invalid value for Docker location")
                should_ask = True

            if not self.test_agent_docker_cgroup(agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port,
                                                 use_tls, local_location, cgroups_location):
                self._display_warning("- Invalid location for cgroup")
                should_ask = True

            if not should_ask:
                self._display_info("- Values for cgroup and remote Docker location are valid.")
            else:
                should_ask = self._ask_with_default("An error happened. Would you like to retry", True)

        # Test the agent port
        while True:
            self._display_info("- Testing the agent port. This can take time.")
            if not self.test_agent_port(agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port, use_tls, local_location,
                                        cgroups_location):
                self._display_error("Invalid value for the agent port. The port seems not being accessible. "
                                    "Remember to open the port in the firewall.")
                if not self._ask_with_default("Do you want to retry?", True):
                    break
                agent_port = self._ask_with_default("Agent port", "63456")
            else:
                self._display_info("- Agent port valid. The remote agent correctly started!")
                break

        # Test the agent remote debug port
        while agent_ssh_port:
            self._display_info("- Testing the agent remote debugging port. This can take time.")
            if not self.test_agent_ssh_port(agent_id, agent_port, agent_ssh_port, remote_host, remote_docker_port, use_tls, local_location,
                                            cgroups_location):
                self._display_error("Invalid value for the agent remote debugging port. The port seems not being accessible. "
                                    "Remember to open the port in the firewall.")
                if not self._ask_with_default("Do you want to retry?", True):
                    agent_ssh_port = None
                else:
                    agent_ssh_port = self._ask_with_default("Remote debugging port", "63456")
            else:
                self._display_info("- Remote debugging port valid.")
                break

        # Hey, we are done!
        self._display_info("- Configuration of the agent succeeded.")
        self._display_question("")
        return {
            "remote_host": remote_host,
            "remote_docker_port": remote_docker_port,
            "remote_agent_port": agent_port,
            "remote_agent_ssh_port": agent_ssh_port,
            "use_tls": use_tls,
            "local_location": local_location,
            "cgroups_location": cgroups_location,
            "agent_name": agent_id
        }

    #######################################
    #       MONGODB CONFIGURATION         #
    #######################################

    def try_mongodb_opts(self, host="localhost", database_name='INGInious'):
        """ Try MongoDB configuration """
        try:
            mongo_client = MongoClient(host=host)
        except Exception as e:
            self._display_warning("Cannot connect to MongoDB on host %s: %s" % (host, str(e)))
            return False

        try:
            database = mongo_client[database_name]
        except Exception as e:
            self._display_warning("Cannot access database %s: %s" % (database_name, str(e)))
            return False

        try:
            GridFS(database)
        except Exception as e:
            self._display_warning("Cannot access gridfs %s: %s" % (database_name, str(e)))
            return False

        return True

    def configure_mongodb(self):
        """ Configure MongoDB """
        self._display_info("Trying default configuration")

        host = "localhost"
        database_name = "INGInious"

        should_ask = True
        if self.try_mongodb_opts(host, database_name):
            should_ask = self._ask_boolean("Successfully connected to MongoDB. Do you want to edit the configuration anyway?", False)
        else:
            self._display_info("Cannot guess configuration for MongoDB.")

        while should_ask:
            self._display_question("Please enter the MongoDB host. If you need to enter a password, here is the syntax:")
            self._display_question("mongodb://USERNAME:PASSWORD@HOST:PORT/AUTHENTIFICATION_DATABASE")
            host = self._ask_with_default("MongoDB host", host)
            database_name = self._ask_with_default("Database name", database_name)
            if not self.try_mongodb_opts(host, database_name):
                if self._ask_boolean("Cannot connect to MongoDB. Would you like to continue anyway?", False):
                    break
            else:
                self._display_info("Successfully connected to MongoDB")
                break

        return {"mongo_opt": {"host": host, "database": database_name}}

    #######################################
    #           TASK DIRECTORY            #
    #######################################

    def configure_task_directory(self):
        """ Configure task directory """
        self._display_question("Please choose a directory in which to store the course/task files. By default, the tool will them in the current "
                               "directory")
        task_directory = None
        while task_directory is None:
            task_directory = self._ask_with_default("Task directory", ".")
            if not os.path.exists(task_directory):
                self._display_error("Path does not exists")
                if self._ask_boolean("Would you like to retry?", True):
                    task_directory = None

        if os.path.exists(task_directory):
            self._display_question("The tool can create a test course in order to let you discover INGInious.")
            if self._ask_boolean("Would you like to copy the test course?", True):
                try:
                    shutil.copytree(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tasks', 'test'),
                                    os.path.join(task_directory, 'test'))
                    self._display_info("Successfully copied the test course")
                except Exception as e:
                    self._display_error("An error occured while copying the directory: %s" % str(e))
        else:
            self._display_warning("Skipping copying the 'test' course because the task dir does not exists")

        return {"tasks_directory": task_directory}

    #######################################
    #             CONTAINERS              #
    #######################################

    def download_container_agent(self, to_download, docker_connection):
        for image in to_download:
            try:
                self._display_info("Downloading image %s. This can take some time." % image)
                docker_connection.pull(image+":latest")
            except Exception as e:
                self._display_error("An error occured while pulling the image: %s." % str(e))

    def download_containers(self, to_download, current_options):
        """ Download the chosen containers on all the agents """
        if current_options["backend"] == "local":
            self._display_info("Connecting to the local Docker daemon...")
            try:
                docker_connection = docker.Client(**kwargs_from_env())
            except:
                self._display_error("Cannot connect to local Docker daemon. Skipping download.")
                return

            self.download_container_agent(to_download, docker_connection)
        elif current_options["backend"] == "remote":
            for daemon in current_options["docker_daemons"]:
                remote_host = daemon["remote_host"]
                remote_docker_port= daemon["remote_docker_port"]
                use_tls = daemon["use_tls"]

                if isinstance(use_tls, basestring):
                    tls_config = docker.tls.TLSConfig(
                        client_cert=(use_tls + '/cert.pem', use_tls + '/key.pem'),
                        verify=use_tls + '/ca.pem'
                    )
                    protocol = "https"
                elif use_tls is True:
                    tls_config = True
                    protocol = "https"
                else:
                    tls_config = False
                    protocol = "http"

                try:
                    docker_connection = docker.Client(base_url=protocol + "://" + remote_host + ":" + str(remote_docker_port), tls=tls_config)
                except:
                    self._display_error("Cannot connect to distant Docker daemon. Skipping download.")
                    continue

                self.download_container_agent(to_download, docker_connection)
        else:
            self._display_warning("This installation tool does not support the backend remote_manual directly. You will have to pull the images by "
                                  "yourself. Here is the list: %s" % str(to_download))

    def configure_containers(self, current_options):
        """ Configures the container dict """
        containers = [
            ("default","Default container. For Bash and Python 2 tasks"),
            ("cpp", "Contains gcc and g++ for compiling C++"),
            ("java7", "Contains Java 7"),
            ("java8scala", "Contains Java 8 and Scala"),
            ("mono", "Contains Mono, which allows to run C#, F# and many other languages"),
            ("oz", "Contains Mozart 2, an implementation of the Oz multi-paradigm language, made for education"),
            ("php", "Contains PHP 5"),
            ("pythia0compat", "Compatibility container for Pythia 0"),
            ("pythia1compat", "Compatibility container for Pythia 1"),
            ("python3", "Contains Python 3"),
            ("r", "Can run R scripts"),
            ("sekexe", "Can run an user-mode-linux for advanced tasks")
        ]

        default_download = ["default", "mono", "java7"]

        self._display_question("The tool will now propose to download some base container image for multiple languages.")
        self._display_question("Please note that the download of these images can take a lot of time, so choose only the images you need")

        options = {"containers": {}}
        to_download = []
        for container_name, description in containers:
            if self._ask_boolean("Download %s (%s) ?" % (container_name, description), container_name in default_download):
                to_download.append("ingi/inginious-c-%s" % container_name)
                options["containers"][container_name] = "ingi/inginious-c-%s" % container_name

        self.download_containers(to_download, current_options)

        wants = self._ask_boolean("To you want to manually add some images?", False)
        while wants:
            image = self._ask_with_default("Container image name (leave this field empty to skip)", "")
            if image == "":
                break
            alias = self._ask_with_default("Container alias in INGInious tasks", image)
            options["containers"][alias] = image

        self._display_info("Configuration of the containers done.")
        return options

    #######################################
    #                MISC                 #
    #######################################

    def configure_misc(self):
        """ Configure various things """
        options = {}
        options["use_minified_js"] = self._ask_boolean("Use minified javascript? (Useful in production, but should be disabled in dev environment)",
                                                       True)

        return options