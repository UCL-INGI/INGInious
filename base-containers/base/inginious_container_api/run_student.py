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

    return "ok"


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
