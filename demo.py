# coding=utf-8
import asyncio
import logging

import time
from zmq.asyncio import ZMQEventLoop, Context

from backend4.messages import BackendBatchJobStarted, BackendBatchJobDone, BackendJobStarted, BackendJobDone, BackendJobSSHDebug
from inginious.common.course_factory import create_factories
from inginious.agent4.docker_agent import DockerAgent
from inginious.agent4.mcq_agent import MCQAgent
from inginious.backend4.backend import Backend
from inginious.backend4.client import Client
import threading

def run_asyncio(loop):
    try:
        asyncio.set_event_loop(loop)
        loop.run_forever()
        loop.close()
    except KeyboardInterrupt:
        print('\nFinished (interrupted)')

def callback_test(result):
    print(result)

def main():
    loop = ZMQEventLoop()
    course_factory, task_factory = create_factories("./inginious/tasks")

    logger = logging.getLogger("inginious")
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    loop.set_debug(1)
    asyncio.set_event_loop(loop)
    context = Context()
    backend = Backend(context, "tcp://127.0.0.1:2222", "tcp://127.0.0.1:2223")
    client = Client(context, "tcp://127.0.0.1:2223")
    agent_docker = DockerAgent(context, "tcp://127.0.0.1:2222", 3, "./inginious/tasks", None)
    agent_mcq = MCQAgent(context, "tcp://127.0.0.1:2222", course_factory)
    asyncio.ensure_future(agent_docker.run_dealer())
    asyncio.ensure_future(agent_mcq.run_dealer())
    asyncio.ensure_future(backend.run())
    client.start()

    t = threading.Thread(target=run_asyncio, args=(loop,))
    t.start()

    time.sleep(5)
    client.new_job(course_factory.get_task("test", "helloworld"), {"question1": "print('Hello World!')"}, callback_test)



if __name__ == "__main__":
    main()