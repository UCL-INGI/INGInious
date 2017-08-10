# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import inspect

import msgpack


class MessageMeta(type):
    """
        A MetaClass for messages

        Provides message checking on both side of the communication.

        Each class depending from this MetaClass MUST have a __init__ function that takes only
        arguments that are type-hinted, and that ONLY assign the argument to self, under the SAME
        name.

        Moreover, the class should define a argument `msgtype` for the metaclass, that gives the name
        of the message when parsed

        Example:

        class SendNumberToContainer(metaclass=MessageMeta, msgtype="send_nbr_container"):
            def __init__(self, container_id: str, a_number: int):
                self.container_id = container_id
                self.a_number = a_number
    """
    _registered_messages = {}
    DEBUG = True

    def __new__(cls, name, bases, namespace, **kargs):  # pylint: disable=unused-argument
        return super().__new__(cls, name, bases, namespace)

    @classmethod
    def load(cls, bmessage):
        """
        From a bytestring given by a (distant) call to Message.dump(), retrieve the original message
        :param bmessage: bytestring given by a .dump() call on a message
        :return: the original message
        """
        message_dict = msgpack.loads(bmessage, encoding="utf8", use_list=False)

        try:
            obj = MessageMeta._registered_messages[message_dict["type"]].__new__(MessageMeta._registered_messages[message_dict["type"]])
            object.__setattr__(obj, "__dict__", message_dict)
        except:
            raise TypeError("Unknown message type") from None

        if not obj._verify():  # pylint: disable=protected-access
            raise TypeError("Invalid message content")

        return obj

    def __init__(cls, name, bases, attrs, msgtype):
        """
        Ensure that the new class
        - Provides immutable objects
        - Respects the contract over __init__
        - Verifies types
        - Has a .dump() function
        """
        old_init = cls.__init__
        old_setattr = cls.__setattr__
        old_delattr = cls.__delattr__

        parameters = inspect.signature(old_init).parameters.copy()
        del parameters["self"]  # self is not a real parameter

        # type a reserved field
        if "type" in parameters:
            raise TypeError("'type' is reserved in messages, use another key")

        # check that all types have annotations
        for field in parameters:
            if parameters[field].annotation == inspect._empty:  # pylint: disable=protected-access
                raise TypeError("All types should be annotated")

        MessageMeta._registered_messages[msgtype] = cls

        def new_init(self, *args, **kwargs):
            object.__setattr__(self, "__currently_mutable", True)

            # Get the message content
            message_content = {x[0]: y for (x, y) in zip(parameters.items(), args)}

            # Ask the init function to fill himself __dict__
            old_init(self, *args, **kwargs)

            object.__delattr__(self, "__currently_mutable")

            # Verify that dict has been filled correctly
            if self.__dict__ != message_content:
                raise TypeError("__init__ does not fullfill the contract of messages. All fields must be init in the object and have the same value "
                                "and name than in the parameters")

            # Do not forget to add message name now
            object.__setattr__(self, "type", msgtype)

        def new_delattr(self, name):
            if "__currently_mutable" in self.__dict__:
                old_delattr(self, name)
            else:
                raise TypeError("Immutable object")

        def new_setattr(self, name, value):
            if "__currently_mutable" in self.__dict__:
                old_setattr(self, name, value)
            else:
                raise TypeError("Immutable object")

        needed_keys = set(parameters.keys()) | {"type"}

        def _verify(self, force=False):
            """
            Ensure this message is consistent with its definition. Verifies only if force or MessageMeta.DEBUG is True
            :param force:
            :return: True if correct, False else
            """
            if force or MessageMeta.DEBUG:
                content_present = set(self.__dict__.keys()) == needed_keys
                type_ok = self.type == msgtype
                return content_present and type_ok
            return True

        def dump(self):
            """
            :return: a bytestring containing a black-box representation of the message, that can be loaded using MessageMeta.load.
            """
            return msgpack.dumps(self.__dict__, encoding="utf8", use_bin_type=True)

        super().__init__(name, bases, attrs)

        cls.__init__ = new_init
        cls.__delattr__ = new_delattr
        cls.__setattr__ = new_setattr
        cls._verify = _verify
        cls.dump = dump
        cls.__msgtype__ = msgtype


def run_tests():
    class StartContainer(metaclass=MessageMeta, msgtype="start_container"):
        def __init__(self, job_id: str, container_name: str):
            self.job_id = job_id
            self.container_name = container_name

    class KillContainer(metaclass=MessageMeta, msgtype="kill_container"):
        def __init__(self, container_id: str):
            self.container_id = container_id

    print("----------------- Verify basic instantiation")
    obj = StartContainer("test", "test2")
    print(obj.job_id)
    assert obj.job_id == "test"
    print(obj.container_name)
    assert obj.container_name == "test2"
    print()

    print("----------------- Verify basic instantiation(2)")
    obj2 = KillContainer("test3")
    print(type(obj2))
    assert type(obj2) == KillContainer
    print(obj2.container_id)
    assert obj2.container_id == "test3"
    print()

    print("----------------- Dump test")
    obj2_dump = obj2.dump()  # pylint: disable=no-member
    print(obj2_dump)
    print()

    print("----------------- Load test")
    obj3 = MessageMeta.load(obj2_dump)
    print(type(obj3))
    assert type(obj3) == KillContainer
    print(obj3.container_id)
    assert obj3.container_id == "test3"
    print()

    print("----------------- Assignation test")
    try:
        obj3.x = "a"
        print("does not work")
    except Exception as e:
        print(e)
        print("(works)")
    print()

    print("----------------- Invalid dump 1 (invalid type)")
    try:
        invalid_dump1 = b'\x82\xaccontainer_id\x01\xa4type\xaekill_containeI'
        obj4 = MessageMeta.load(invalid_dump1)
        print(type(obj4))
        print(obj4.container_id)
        print("does not work")
    except TypeError as e:
        print(e)
        print("(works)")
    print()

    print("----------------- Invalid dump 2 (invalid fields)")
    try:
        invalid_dump2 = b'\x82\xaccontainer_iI\x01\xa4type\xaekill_container'
        obj5 = MessageMeta.load(invalid_dump2)
        print(type(obj5))
        print(obj5.container_id)
        print("does not work")
    except KeyError as e:
        print(e)
        print("(works)")
    print()

    print("----------------- Invalid dump 3 (invalid content)")
    try:
        invalid_dump3 = msgpack.dumps({"type": "kill_container", "container_id": 2}, encoding="utf8")
        obj6 = MessageMeta.load(invalid_dump3)
        print(type(obj6))
        print(obj6.container_id)
        print("does not work")
    except TypeError as e:
        print(e)
        print("(works)")
    print()


class ZMQUtils(object):
    """
        Utilities that do serializing/unserializing of messages (whose metaclass is MessageMeta)
    """

    @classmethod
    async def recv_with_addr(cls, socket):
        message = await socket.recv_multipart()
        addr = message[0]
        obj = MessageMeta.load(message[1])
        return addr, obj

    @classmethod
    async def send_with_addr(cls, socket, addr: bytes, obj):
        message = [addr, obj.dump()]
        await socket.send_multipart(message)

    @classmethod
    async def recv(cls, socket, skip_first=False):
        message = await socket.recv_multipart()
        return MessageMeta.load(message[0] if not skip_first else message[1])

    @classmethod
    async def send(cls, socket, obj, send_white=False):
        message_obj = obj.dump()
        await socket.send_multipart([message_obj] if not send_white else ["", message_obj])
