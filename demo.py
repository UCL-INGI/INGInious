# coding=utf-8
import asyncio
import logging

import time
from zmq.asyncio import ZMQEventLoop, Context

from inginious.common.messages import BackendBatchJobStarted, BackendBatchJobDone, BackendJobStarted, BackendJobDone, BackendJobSSHDebug
from inginious.common.course_factory import create_factories
from inginious.agent4.docker_agent import DockerAgent
from inginious.agent4.mcq_agent import MCQAgent
from inginious.backend4.backend import Backend
from inginious.backend4.client import Client
import threading

def run_asyncio(loop, context_1, context_2):
    try:
        asyncio.set_event_loop(loop)
        loop.run_forever()
    except:
        logging.getLogger("inginious").exception("")
        print('\nFinished (interrupted)')
    finally:
        loop.close()
        context_1.destroy()
        context_2.destroy()

def callback_test(result):
    callback_test.i += 1
    print(str(result) + "\t" + str(callback_test.i))
    if result[0] != "success":
        exit(1)

callback_test.i = 0

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
    context_1 = Context()
    context_2 = Context()
    backend = Backend(context_1, "tcp://127.0.0.1:2222", "tcp://127.0.0.1:2223")
    client = Client(context_1, "tcp://127.0.0.1:2223")
    agent_docker_1 = DockerAgent(context_1, "tcp://127.0.0.1:2222", 3, "./inginious/tasks", None, tmp_dir="./agent_tmp_1")
    agent_docker_2 = DockerAgent(context_2, "tcp://127.0.0.1:2222", 3, "./inginious/tasks", None, tmp_dir="./agent_tmp_2")
    agent_mcq = MCQAgent(context_1, "tcp://127.0.0.1:2222", course_factory)
    asyncio.ensure_future(agent_docker_1.run_dealer())
    asyncio.ensure_future(agent_docker_2.run_dealer())
    asyncio.ensure_future(agent_mcq.run_dealer())
    asyncio.ensure_future(backend.run())
    client.start()

    t = threading.Thread(target=run_asyncio, args=(loop, context_1, context_2))
    t.start()

    time.sleep(5)
    for i in range(0, 10):
        client.new_job(course_factory.get_task("test", "helloworld"), {"question1": "print('Hello World!')"}, callback_test)

    try:
        t.join()
    except:
        pass
    finally:
        loop.stop()



if __name__ == "__main__":
    main()