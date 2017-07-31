# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Shared methods for the command line tool that installs the frontends """
import abc
import os
import tarfile
import urllib.request

import docker
from docker.utils import kwargs_from_env
from gridfs import GridFS
from pymongo import MongoClient

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


class Installer(object, metaclass=abc.ABCMeta):
    def __init__(self, config_path=None):
        self._config_path = config_path

    #######################################
    #          Display functions          #
    #######################################

    def _display_header(self, title):
        """ Displays an header in the console """
        print("")
        print(BOLD + HEADER + "--- " + title + " ---" + ENDC)

    def _display_warning(self, content):
        """ Displays a warning in the console """
        print(WARNING + "(WARN) " + content + ENDC)

    def _display_info(self, content):
        """ Displays an info message in the console """
        print(INFO + "(INFO) " + content + ENDC)

    def _display_question(self, content):
        """ Displays a preamble to a question """
        print(DOC + content + ENDC)

    def _display_error(self, content):
        """ Displays an error """
        print(WHITE + BACKGROUND_RED + "(ERROR) " + content + ENDC)

    def _display_big_warning(self, content):
        """ Displays a BIG warning """
        print("")
        print(BOLD + WARNING + "--- WARNING ---" + ENDC)
        print(WARNING + content + ENDC)
        print("")

    def _ask_with_default(self, question, default):
        default = str(default)
        answer = input(DOC + UNDERLINE + question + " [" + default + "]:" + ENDC + " ")
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
        self._display_header("BACKEND CONFIGURATION")
        options = {}
        while True:
            options = {}
            backend = self.ask_backend()
            if backend == "local":
                self._display_info("Backend chosen: local. Testing the configuration.")
                options = self._ask_local_config()
                if not self.test_local_docker_conf():
                    self._display_error("An error occurred while testing the configuration. Please make sure you are able do run `docker info` in "
                                        "your command line, and environment parameters like DOCKER_HOST are correctly set.")
                    if self._ask_boolean("Would you like to continue anyway?", False):
                        break
                else:
                    break
            else:
                self._display_warning("Backend chosen: manual. As it is a really advanced feature, you will have to configure it yourself in "
                                      "the configuration file, at the end of the setup process.")
                options = {"backend": backend}
                break

        self._display_header("MONGODB CONFIGURATION")
        mongo_opt = self.configure_mongodb()
        options.update(mongo_opt)

        self._display_header("TASK DIRECTORY")
        task_directory_opt = self.configure_task_directory()
        options.update(task_directory_opt)

        self._display_header("CONTAINERS")
        self.configure_containers(options)

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
            print(yaml.dump(options))

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

    def _ask_local_config(self):
        """ Ask some parameters about the local configuration """
        options = {"backend": "local", "local-config": {}}

        # Concurrency
        while True:
            concurrency = self._ask_with_default("Maximum concurrency (number of tasks running simultaneously). Leave it empty to use the number of "
                                                 "CPU of your host.", "")
            if concurrency == "":
                break

            try:
                concurrency = int(concurrency)
            except:
                self._display_error("Invalid number")
                continue

            if concurrency <= 0:
                self._display_error("Invalid number")
                continue

            options["local-config"]["concurrency"] = concurrency
            break

        # Debug hostname
        hostname = self._ask_with_default("What is the external hostname/address of your machine? You can leave this empty and let INGInious "
                                        "autodetect it.", "")
        if hostname != "":
            options["local-config"]["debug_host"] = hostname
        self._display_info("You can now enter the port range for the remote debugging feature of INGInious. Please verify that these "
                                        "ports are open in your firewall. You can leave this parameters empty, the default is 64100-64200")

        # Debug port range
        port_range = None
        while True:
            start_port = self._ask_with_default("Beginning of the range", "")
            if start_port != "":
                try:
                    start_port = int(start_port)
                except:
                    self._display_error("Invalid number")
                    continue
                end_port = self._ask_with_default("End of the range", str(start_port+100))
                try:
                    end_port = int(end_port)
                except:
                    self._display_error("Invalid number")
                    continue
                if start_port > end_port:
                    self._display_error("Invalid range")
                    continue
                port_range = str(start_port)+"-"+str(end_port)
            else:
                break
        if port_range != None:
            options["local-config"]["debug_ports"] = port_range

        return options

    def test_local_docker_conf(self):
        """ Test to connect to a local Docker daemon """
        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except Exception as e:
            self._display_error("- Unable to connect to Docker. Error was %s" % str(e))
            return False

        try:
            self._display_info("- Asking Docker some info")
            if docker.utils.compare_version('1.24', docker_connection.version()['ApiVersion']) < 0:
                self._display_error("- Docker version >= 1.12.0 is required.")
                return False
        except Exception as e:
            self._display_error("- Unable to contact Docker. Error was %s" % str(e))
            return False
        self._display_info("- Successfully got info from Docker. Docker connection works.")

        return True

    def ask_backend(self):
        """ Ask the user to choose the backend """
        response = self._ask_boolean("Do you have a local docker daemon (on Linux), do you use docker-machine via a local machine, or do you use "
                                     "Docker for macOS?", True)
        if(response):
            self._display_info("If you use docker-machine on macOS, please see "
                               "http://inginious.readthedocs.io/en/latest/install_doc/troubleshooting.html")
            return "local"
        else:
            self._display_info("You will have to run inginious-backend and inginious-agent yourself. Please run the commands without argument "
                               "and/or read the documentation for more info")
            return self._display_question("Please enter the address of your backend")

    #######################################
    #       MONGODB CONFIGURATION         #
    #######################################

    def try_mongodb_opts(self, host="localhost", database_name='INGInious'):
        """ Try MongoDB configuration """
        try:
            mongo_client = MongoClient(host=host)
        except Exception as e:
            self._display_warning("Cannot connect to MongoDB on host %s: %s" % (host, str(e)))
            return None

        try:
            database = mongo_client[database_name]
        except Exception as e:
            self._display_warning("Cannot access database %s: %s" % (database_name, str(e)))
            return None

        try:
            GridFS(database)
        except Exception as e:
            self._display_warning("Cannot access gridfs %s: %s" % (database_name, str(e)))
            return None

        return database

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
        self._display_question("Please choose a directory in which to store the course/task files. By default, the tool will put them in the current "
                               "directory")
        task_directory = None
        while task_directory is None:
            task_directory = self._ask_with_default("Task directory", ".")
            if not os.path.exists(task_directory):
                self._display_error("Path does not exists")
                if self._ask_boolean("Would you like to retry?", True):
                    task_directory = None

        if os.path.exists(task_directory):
            self._display_question("Demonstration tasks can be downloaded to let you discover INGInious.")
            if self._ask_boolean("Would you like to download them ?", True):
                try:
                    filename, _ = urllib.request.urlretrieve("https://api.github.com/repos/UCL-INGI/INGInious-demo-tasks/tarball")
                    with tarfile.open(filename, mode="r:gz") as thetarfile:
                        members = thetarfile.getmembers()
                        commonpath = os.path.commonpath([tarinfo.name for tarinfo in members])

                        for member in members:
                            member.name = member.name[len(commonpath) + 1:]
                            if member.name:
                                thetarfile.extract(member, task_directory)

                    self._display_info("Successfully downloaded and copied demonstration tasks.")
                except Exception as e:
                    self._display_error("An error occurred while copying the directory: %s" % str(e))
        else:
            self._display_warning("Skipping copying the 'test' course because the task dir does not exists")

        return {"tasks_directory": task_directory}

    #######################################
    #             CONTAINERS              #
    #######################################

    def download_containers(self, to_download, current_options):
        """ Download the chosen containers on all the agents """
        if current_options["backend"] == "local":
            self._display_info("Connecting to the local Docker daemon...")
            try:
                docker_connection = docker.Client(**kwargs_from_env())
            except:
                self._display_error("Cannot connect to local Docker daemon. Skipping download.")
                return

            for image in to_download:
                try:
                    self._display_info("Downloading image %s. This can take some time." % image)
                    docker_connection.pull(image + ":latest")
                except Exception as e:
                    self._display_error("An error occurred while pulling the image: %s." % str(e))
        else:
            self._display_warning("This installation tool does not support the backend configuration directly, if it's not local. You will have to "
                                  "pull the images by yourself. Here is the list: %s" % str(to_download))

    def configure_containers(self, current_options):
        """ Configures the container dict """
        containers = [
            ("default", "Default container. For Bash and Python 2 tasks"),
            ("cpp", "Contains gcc and g++ for compiling C++"),
            ("java7", "Contains Java 7"),
            ("java8scala", "Contains Java 8 and Scala"),
            ("mono", "Contains Mono, which allows to run C#, F# and many other languages"),
            ("oz", "Contains Mozart 2, an implementation of the Oz multi-paradigm language, made for education"),
            ("php", "Contains PHP 5"),
            ("pythia0compat", "Compatibility container for Pythia 0"),
            ("pythia1compat", "Compatibility container for Pythia 1"),
            ("r", "Can run R scripts"),
            ("sekexe", "Can run an user-mode-linux for advanced tasks")
        ]

        default_download = ["default"]

        self._display_question("The tool will now propose to download some base container image for multiple languages.")
        self._display_question("Please note that the download of these images can take a lot of time, so choose only the images you need")

        to_download = []
        for container_name, description in containers:
            if self._ask_boolean("Download %s (%s) ?" % (container_name, description), container_name in default_download):
                to_download.append("ingi/inginious-c-%s" % container_name)

        self.download_containers(to_download, current_options)

        wants = self._ask_boolean("Do you want to manually add some images?", False)
        while wants:
            image = self._ask_with_default("Container image name (leave this field empty to skip)", "")
            if image == "":
                break

        self._display_info("Configuration of the containers done.")

    #######################################
    #                MISC                 #
    #######################################

    def configure_misc(self):
        """ Configure various things """
        options = {}
        options["use_minified_js"] = self._ask_boolean("Use minified javascript? (Useful in production, but should be disabled in dev environment)",
                                                       True)

        return options
