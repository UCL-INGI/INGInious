# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import asyncio
import docker
from docker.utils import kwargs_from_env


class DockerTransfertProtocolClient(asyncio.Protocol):
    def __init__(self, out):
        self.out = out

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):

        # Check that the main transport has not closed yet
        if self.out.is_closing():
            self.transport.close()
            return

        self.out.write(data)


class DockerTransfertProtocolClientIn(asyncio.Protocol):
    def __init__(self, set_transport):
        self.set_transport = set_transport

    def connection_made(self, transport):
        self.set_transport(transport)

class DockerTransferProtocolServer(asyncio.Protocol):
    def __init__(self, event_loop, parent_container_id, container_set, student_path, default_container, default_time, default_memory,
                 create_new_student_container, student_container_get_stdX, student_container_signal, student_container_close):
        self._event_loop = event_loop
        self._docker_client = docker.Client(**kwargs_from_env())
        self._parent_container_id = parent_container_id
        self._container_set = container_set
        self._student_path = student_path
        self._default_container = default_container
        self._default_time = default_time
        self._default_memory = default_memory
        self._create_new_student_container = create_new_student_container
        self._student_container_get_stdX = student_container_get_stdX
        self._student_container_signal = student_container_signal
        self._student_container_close = student_container_close

    def connection_made(self, transport):
        """
        Called when a connection is made.
        The argument is the transport representing the pipe connection.
        To receive data, wait for data_received() calls.
        When the connection is closed, connection_lost() is called.
        """
        self.transport = transport
        self.mode = 0  # waiting for instructions
        self.stdin_conn = None
        self.stdin_transport = None
        self.buffer = b""

    def data_received(self, data):
        """
        Called when some data is received.
        The argument is a bytes object.
        """
        if self.mode == 0:  # waiting for instructions
            self.buffer += data
            if "\r\n" in self.buffer:
                commands = self.buffer.split(b"\r\n")
                toparse = commands[0]
                self.buffer = b""
                self._dispatch(toparse)
                if len(commands) > 1:
                    self.data_received(b"\r\n".join(commands[1:]))  # repeat to be sure we empty the buffer if needed
        elif self.mode == 1:  # redirect
            self._handle_stdin_redirect(data)
        elif self.mode == 2:  # done
            pass

    def _dispatch(self, data):
        try:
            if data.startwith(b"run"):
                self._handle_run(data)
            elif data.startwith(b"stdout") or data.startwith(b"stderr"):
                self._handle_stdX(data)
            elif data.startwith(b"stdin"):
                self._handle_stdin(data)
            elif data.startwith(b"signal"):
                self._handle_signal(data)
            elif data.startwith(b"close"):
                self._handle_close(data)
            else:
                raise Exception("Unknown command")
        except Exception as e:
            self.transport.write(b"error|" + str(e).encode("utf8") + "\r\n")
            self.transport.close()

    def _handle_signal(self, data):
        data = data.split(b"|")
        self._ensure_containerid(data[1])
        self.transport.write(b"ok|" + str(int(self._student_container_signal(data[1], int(data[2])))).encode("utf8") + b"\r\n")
        self.mode = 2  # done

    def _handle_close(self, data):
        data = data.split(b"|")
        self._ensure_containerid(data[1])
        self.transport.write(b"ok|" + str(int(self._student_container_close(data[1]))).encode("utf8") + b"\r\n")
        self.mode = 2  # done

    def _handle_stdin(self, data):
        data = data.split(b"|")
        self._ensure_containerid(data[1])
        socket = self._student_container_get_stdX(data[1], stdin=True, stdout=False, stderr=False)
        self.std_conn = self._event_loop.create_connection(lambda: DockerTransfertProtocolClientIn(self._set_stdin_transport),
                                                           sock=socket)

        self._event_loop.create_task(self.std_conn)
        self.mode = 1  # stdin

    def _handle_stdX(self, data):
        data = data.split(b"|")
        stdout = False
        stderr = False
        if data[0] == b"stdout":
            stdout = True
        elif data[1] == b"stderr":
            stderr = True
        else:
            raise Exception("unknown operation")
        self._ensure_containerid(data[1])
        socket = self._student_container_get_stdX(data[1], stdin=False, stdout=stdout, stderr=stderr)
        conn = self._event_loop.create_connection(lambda: DockerTransfertProtocolClient(self.transport), sock=socket)
        self._event_loop.create_task(conn)
        self.mode = 2  # stdout/stderr

    def _handle_stdin_redirect(self, data):
        self.stdin_transport.write(data)  # transmit data

    def _handle_run(self, data):
        _, container_name, working_dir, command, memory_limit, time_limit, hard_time_limit, share_network = data.decode("utf8").split("|")
        if container_name == "":
            container_name = self._default_container
        if memory_limit == 0:
            memory_limit = self._default_memory
        if time_limit == 0:
            time_limit = self._default_time
        if hard_time_limit == 0:
            hard_time_limit = 3 * time_limit
        container_id, error = self._create_new_student_container(str(container_name), str(working_dir), str(command), int(memory_limit),
                                                                 int(time_limit), int(hard_time_limit), bool(share_network),
                                                                 self._parent_container_id, self._parent_container_id,
                                                                 self._parent_container_id)
        if error is not None:
            self.transport.write(b"error|" + error.encore("utf8") + b"\r\n")
        else:
            self.transport.write(b"ok|" + str(container_id).encode("utf8") + b"\r\n")

    def _ensure_containerid(self, container_id):
        if container_id not in self._container_set:
            raise Exception("Invalid container id")

    def _set_stdin_transport(self, t):
        self.stdin_transport = t
        self.transport.resume_reading()