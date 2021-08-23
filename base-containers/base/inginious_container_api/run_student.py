# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import array
import os
import signal
import socket
import tempfile
import asyncio
import zmq.asyncio
import msgpack
import zmq
import struct


def run_student(cmd, container=None,
        time_limit=0, hard_time_limit=0,
        memory_limit=0, share_network=False,
        working_dir=None, stdin=None, stdout=None, stderr=None,
        signal_handler_callback=None, ssh=False, run_as_root=False, teardown_script=""):
    """
    Run a command inside a student container

    :param cmd: command to be ran (as a string, with parameters). If ssh is set to True, this command will be run before launching the ssh server.
    :param container: container to use. Must be present in the current agent. By default it is None, meaning the current
                      container type will be used.
    :param time_limit: time limit in seconds. By default it is 0, which means that it will be the same as the current
                       container (NB: it does not count in the "host" container timeout!)
    :param hard_time_limit: hard time limit. By default it is 0, which means that it will be the same as the current
                       container (NB: it *does* count in the "host" container *hard* timeout!)
    :param memory_limit: memory limit in megabytes. By default it is 0, which means that it will be the same as the current
                       container (NB: it does not count in the "host" container memory limit!)
    :param share_network: share the network with the host container if True. Default is False.
    :param working_dir: The working directory for the distant command. By default, it is os.getcwd().
    :param stdin: File descriptor for stdin. Can be None, in which case a file descriptor is open to /dev/null.
    :param stdout: File descriptor for stdout. Can be None, in which case a file descriptor is open to /dev/null.
    :param stderr: File descriptor for stderr. Can be None, in which case a file descriptor is open to /dev/null.
    :param signal_handler_callback: If not None, `run` will call this callback with a function as single argument.
                                    this function can itself be called with a signal value that will immediately be sent
                                    to the remote process. See the run_student script command for an example, or
                                    the hack_signals function below.
    :param ssh: If set to True, it starts an ssh server for the student after the command finished.
    :param run_as_root: If set to True, it tries to execute the command as root (for ssh, it accepts connection as root).
                        Default is False. This is a Beta feature and should not be used yet.
    :param teardown_script:  command to be ran (as a string, with parameters) in the student container before closing it.
                            This parameter is mainly useful when ssh is set to True.
    :remark Calling run_student on a grading container running as root with Kata is not a possible feature yet.
    :return: the return value of the calling process. There are special values:
        - 251 means that run_student is not available in this container/environment
        - 252 means that the command was killed due to an out-of-memory
        - 253 means that the command timed out
        - 254 means that an error occurred while running the proxy
    """

    #  Checking runtimes
    shared_kernel = os.path.exists("/.__input/__shared_kernel")
    only_dockers = shared_kernel and not run_as_root
    user = "root" if run_as_root else "worker"
    #  Basic files management
    if working_dir is None:
        working_dir = os.getcwd()
    if stdin is None:
        stdin = open(os.devnull, 'rb').fileno()
    if stdout is None:
        stdout = open(os.devnull, 'rb').fileno()
    if stderr is None:
        stderr = open(os.devnull, 'rb').fileno()

    try:
        server, socket_id, socket_path, path = create_student_socket(only_dockers)
        zmq_socket, student_container_id = start_student_container(container, time_limit, hard_time_limit, memory_limit, share_network, socket_id, ssh, run_as_root)
        connection = send_initial_command(socket_id, server, stdin, stdout, stderr, zmq_socket, student_container_id, cmd, teardown_script, working_dir, ssh, user, only_dockers)
        allow_to_send_signals(signal_handler_callback, connection, student_container_id, only_dockers)



        return "temporary_return_value"
    except:
        return 254


def run_student_simple(cmd, cmd_input=None, container=None,
        time_limit=0, hard_time_limit=0,
        memory_limit=0, share_network=False,
        working_dir=None, stdout_err_fuse=False, text="utf-8"):
    """
    A simpler version of `run`, which takes an input string and return the output of the command.
    This disallows interactive processes.

    :param cmd: cmd to be run.
    :param cmd_input: input of the command. Can be a string or a bytes object, or None.
    :param container: container to use. Must be present in the current agent. By default it is None, meaning the current
                      container type will be used.
    :param time_limit: time limit in seconds. By default it is 0, which means that it will be the same as the current
                       container (NB: it does not count in the "host" container timeout!)
    :param hard_time_limit: hard time limit. By default it is 0, which means that it will be the same as the current
                       container (NB: it *does* count in the "host" container *hard* timeout!)
    :param memory_limit: memory limit in megabytes. By default it is 0, which means that it will be the same as the current
                       container (NB: it does not count in the "host" container memory limit!)
    :param share_network: share the network with the host container if True. Default is False.
    :param working_dir: The working directory for the distant command. By default, it is os.getcwd().
    :param stdout_err_fuse: Weither to fuse stdout and stderr (i.e. make them use the same file descriptor)
    :param text: By default, run_simple assumes that stdout/stderr will be encoded in UTF-8. Putting another encoding
                 will make the streams encoded using this encoding. text=False indicates that the streams should be
                 opened in binary mode. In this case, run_simple returns streams in the form of binary, unencoded,
                 strings.
    :return: The output of the command, as a tuple of objects (stdout, stderr, retval). If stdout_err_fuse is True, the
             output is in the form (stdout, retval) is returned.
             The type of the returned strings (stdout, stderr) is dependent of the `text` arg.
    """
    stdin = None
    if cmd_input is not None:
        r, w = os.pipe()
        fdo = os.fdopen(w, 'w')
        fdo.write(cmd_input)
        fdo.close()
        stdin = r

    stdout_r, stdout_w = os.pipe()
    if stdout_err_fuse:
        stderr_r, stderr_w = stdout_r, stdout_w
    else:
        stderr_r, stderr_w = os.pipe()

    retval = run_student(cmd, container, time_limit, hard_time_limit, memory_limit,
                         share_network, working_dir, stdin, stdout_w, stderr_w)

    preprocess_out = (lambda x: x.decode(text)) if text is not False else (lambda x: x)

    os.fdopen(stdout_w, 'w').close()
    stdout = preprocess_out(os.fdopen(stdout_r, 'rb').read())
    if not stdout_err_fuse:
        os.fdopen(stderr_w, 'w').close()
        stderr = preprocess_out(os.fdopen(stderr_r, 'rb').read())
        return stdout, stderr, retval
    else:
        return stdout, retval


######################################################################
######################################################################
########### HELPERS ##################################################
######################################################################
######################################################################

def _hack_signals(receive_signal):
    """ Catch every signal, and send it to the remote process """
    uncatchable = ['SIG_DFL', 'SIGSTOP', 'SIGKILL']
    for i in [x for x in dir(signal) if x.startswith("SIG")]:
        if i not in uncatchable:
            try:
                signum = getattr(signal, i)
                signal.signal(signum, lambda x, _: receive_signal)
            except:
                pass

async def _send_intern_message(send_socket, msg):
    send_socket.send(msgpack.dumps(msg, use_bin_type=True))
    send_socket.recv()


def create_student_socket(both_dockers):
    if both_dockers:
        # creates a placeholder for the socket
        DIR = "/sockets/"
        _, path = tempfile.mkstemp('', 'p', DIR)

        # Gets the socket id
        socket_id = os.path.split(path)[-1]
        socket_path = os.path.join(DIR, socket_id + ".sock")

        # Start the socket
        server = socket.socket(socket.AF_UNIX)
        try:
            os.unlink(socket_path)
        except OSError:
            if os.path.exists(socket_path):
                raise
        server.bind(socket_path)
        server.listen(0)
        return server, socket_id, socket_path, path
    else:
        return None, "socketId", None, None


def start_student_container(container, time_limit, hard_time_limit, memory_limit, share_network, socket_id, ssh, run_as_root):
    # Kindly ask the agent to start a new container linked to our socket
    context = zmq.Context()
    zmq_socket = context.socket(zmq.REQ)
    zmq_socket.connect("ipc:///sockets/main.sock")
    # print("DEBUG:    Sending message asking agent to create student_container")
    zmq_socket.send(msgpack.dumps({"type": "run_student", "environment": container,
                                   "time_limit": time_limit, "hard_time_limit": hard_time_limit,
                                   "memory_limit": memory_limit, "share_network": share_network,
                                   "socket_id": socket_id, "ssh": ssh, "run_as_root": run_as_root},
                                  use_bin_type=True))
    # Check if the container was correctly started
    message = msgpack.loads(zmq_socket.recv(), use_list=False, strict_map_key=False)
    assert message["type"] == "run_student_started"
    student_container_id = message["container_id"]
    return zmq_socket, student_container_id


def send_initial_command(socket_id, server, stdin, stdout, stderr, zmq_socket, student_container_id, cmd, teardown_script, working_dir, ssh, user, both_dockers):
    if both_dockers:
        # The socket only works in a ping-pong style so we need to send a dummy message
        zmq_socket.send(msgpack.dumps({"type": "run_student_ask_retval", "socket_id": socket_id}, use_bin_type=True))

        # Serve one and only one connection
        connection, addr = server.accept()

        # _run_student_intern should say hello
        datagram = connection.recv(1)
        assert datagram == b'H'

        # send the fds and the command/workdir directly to student_container
        connection.sendmsg([b'S'], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [stdin, stdout, stderr]))])
        connection.send(msgpack.dumps(
            {"type": "run_student_command", "student_container_id": student_container_id, "command": cmd,
             "teardown_script": teardown_script, "working_dir": working_dir, "ssh": ssh, "user": user, "only_dockers": both_dockers, "stdin": stdin}))
        return connection

    else:
        # Send the command to the student_container via the agent
        zmq_socket.send(msgpack.dumps(
            {"type": "run_student_command", "student_container_id": student_container_id, "command": cmd,
             "teardown_script": teardown_script, "working_dir": working_dir,
             "ssh": ssh, "user": user, "only_dockers": both_dockers, "stdin": stdin}, use_bin_type=True))
        return None


def allow_to_send_signals(signal_handler_callback, connection, student_container_id, both_dockers):
    if signal_handler_callback is not None:
        if both_dockers:
            def receive_signal(signum_s):  # send signal directly to student_container
                signum_data = str(signum_s).zfill(3).encode("utf8")
                connection.send(signum_data)
        else:
            def receive_signal(signum_s):  # send signal to student_container via docker agent
                signum_data = str(signum_s).zfill(3).encode("utf8")
                msg = {"type": "student_signal", "student_container_id": student_container_id, "signal_data": signum_data}
                send_socket = zmq.asyncio.Context().socket(zmq.REQ)
                send_socket.connect("ipc:///sockets/main.sock")
                send_socket.send(msgpack.dumps(msg, use_bin_type=True))
        signal_handler_callback(receive_signal)

