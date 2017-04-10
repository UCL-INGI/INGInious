# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import logging

import asyncio
import multiprocessing
import threading

from zmq.asyncio import ZMQEventLoop, Context

from inginious.common.filesystems.local import LocalFSProvider
from inginious.agent.docker_agent import DockerAgent
from inginious.agent.mcq_agent import MCQAgent
from inginious.backend.backend import Backend
from inginious.client.client import Client

def start_asyncio_and_zmq():
    """ Init asyncio and ZMQ. Starts a daemon thread in which the asyncio loops run.
    :return: a ZMQ context and a Thread object (as a tuple)
    """
    loop = ZMQEventLoop()
    asyncio.set_event_loop(loop)
    zmq_context = Context()

    t = threading.Thread(target=_run_asyncio, args=(loop, zmq_context), daemon=True)
    t.start()

    return zmq_context, t

def _run_asyncio(loop, zmq_context):
    """
    Run asyncio (should be called in a thread) and close the loop and the zmq context when the thread ends
    :param loop:
    :param zmq_context:
    :return:
    """
    try:
        asyncio.set_event_loop(loop)
        loop.run_forever()
    except:
        pass
    finally:
        loop.close()
        zmq_context.destroy(1000)

def create_arch(configuration, tasks_fs, context):
    """ Helper that can start a simple complete INGInious arch locally if needed, or a client to a remote backend.
        Intended to be used on command line, makes uses of exit() and the logger inginious.frontend.
    :param configuration: configuration dict
    :param tasks_fs: FileSystemProvider to the courses/tasks folders
    :param context: a ZMQ context
    :param is_testing: boolean
    :return: a Client object
    """

    logger = logging.getLogger("inginious.frontend")

    backend_link = configuration.get("backend", "local")
    if backend_link == "local":
        logger.info("Starting a simple arch (backend, docker-agent and mcq-agent) locally")

        local_config = configuration.get("local-config", {})
        concurrency = local_config.get("concurrency", multiprocessing.cpu_count())
        debug_host = local_config.get("debug_host", None)
        debug_ports = local_config.get("debug_ports", None)
        tmp_dir = local_config.get("tmp_dir", "./agent_tmp")

        if debug_ports is not None:
            try:
                debug_ports = debug_ports.split("-")
                debug_ports = range(int(debug_ports[0]), int(debug_ports[1]))
            except:
                logger.error("debug_ports should be in the format 'begin-end', for example '1000-2000'")
                exit(1)
        else:
            debug_ports = range(64100, 64111)

        client = Client(context, "inproc://backend_client")
        backend = Backend(context, "inproc://backend_agent", "inproc://backend_client")
        agent_docker = DockerAgent(context, "inproc://backend_agent", "Docker - Local agent", concurrency, tasks_fs, debug_host, debug_ports, tmp_dir)
        agent_mcq = MCQAgent(context, "inproc://backend_agent", "MCQ - Local agent", tasks_fs)

        asyncio.ensure_future(agent_docker.run_dealer())
        asyncio.ensure_future(agent_mcq.run_dealer())
        asyncio.ensure_future(backend.run())
    elif backend_link in ["remote", "remote_manuel", "docker_machine"]: #old-style config
        logger.error("Value '%s' for the 'backend' option is configuration.yaml is not supported anymore. \n"
                     "Have a look at the 'update' section of the INGInious documentation in order to upgrade your configuration.yaml", backend_link)
        exit(1)
        return None #... pycharm returns a warning else :-(
    else:
        logger.info("Creating a client to backend at %s", backend_link)
        client = Client(context, backend_link)

    # check for old-style configuration entries
    old_style_configs = ["agents", 'containers', "machines", "docker_daemons"]
    for c in old_style_configs:
        if c in configuration:
            logger.warning("Option %s in configuration.yaml is not used anymore.\n"
                           "Have a look at the 'update' section of the INGInious documentation in order to upgrade your configuration.yaml", c)

    return client
