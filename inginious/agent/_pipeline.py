# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

"""
    Pipeline abstraction for ZMQ
"""
import asyncio
from abc import ABCMeta, abstractmethod

import zmq

from inginious.common.message_meta import ZMQUtils


class PipelineBase(object):
    def __init__(self, _context, _name):  # pylint: disable=unused-argument
        super().__init__()


class PipelinePush(PipelineBase):
    """
        Pipeline abstraction around ZMQ.
        This class provides a pipeline socket that push things in the pipeline.
        Use cases are either the first element of the pipeline or internal element, that also have a pull socket
    """

    def __init__(self, context, name):
        super().__init__(context, name)
        self._link = "inproc://pipeline" + name
        self._push = context.socket(zmq.PUSH)
        self._push.bind(self._link)

    def get_link(self):
        """
        :return: the link that allows to subscribe to this PipelineElement
        """
        return self._link

    def get_push_socket(self):
        """
        :return: the push socket
        """
        return self._push


class PipelinePull(PipelineBase):
    """
        Pipeline abstraction around ZMQ.
        This class provides a pipeline socket that pull things from the pipeline.
        Use cases are either the last element of the pipeline or internal element, that also have a push socket
    """

    def __init__(self, context, name):
        super().__init__(context, name)
        self._pull = context.socket(zmq.PULL)

    def link(self, push_element):
        """
        Subscribe this pipeline element to the PipelinePush `push_element`
        """
        self._pull.connect(push_element.get_link())

    def get_pull_socket(self):
        """
        :return: the pull socket
        """
        return self._pull


class PipelineElement(PipelinePush, PipelinePull):
    """
    Pipeline abstraction around ZMQ.
    This class provides a pipeline element, along with methods to link it to other pipeline elements
    """
    __metaclass__ = ABCMeta

    def __init__(self, context, name):
        super().__init__(context, name)

    async def run_pipeline(self):
        """
        Runs the pipeline element
        :return:
        """
        try:
            while True:
                message = await ZMQUtils.recv(self._pull)
                retval = await self._handle_message(message)
                await ZMQUtils.send(self._push, retval)
        except asyncio.CancelledError:
            return
        except KeyboardInterrupt:
            return

    @abstractmethod
    async def _handle_message(self, message):
        """
        :param message: an array (multipart message) containing the message received by the pipeline elemnt
        :return: an array (multipart message) that will be given to the next element of the pipeline
        """
        return message
