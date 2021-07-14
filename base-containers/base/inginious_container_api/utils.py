# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import os
import tempfile
import subprocess
import resource
import stat
import time


def set_limits_user(user):
    if user == "worker":
        os.setgid(4242)
        os.setuid(4242)
    os.environ["HOME"] = "/task"
    resource.setrlimit(resource.RLIMIT_NPROC, (1000, 1000))


def set_executable(filename):
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | stat.S_IEXEC)


def execute_process(args, stdin_string="", internal_command=False, user="worker"):
    if not isinstance(args, list):
        args = [args]
    set_limits = (lambda: set_limits_user(user))
    stdin = tempfile.TemporaryFile()
    stdin.write(stdin_string.encode('utf-8'))
    stdin.seek(0)

    stdout = tempfile.TemporaryFile()
    stderr = tempfile.TemporaryFile()
    if internal_command:
        pr = subprocess.Popen(args, stdin=stdin, stdout=stdout, stderr=stderr)
    else:
        set_executable(args[0])
        pr = subprocess.Popen(args, preexec_fn=set_limits, stdin=stdin, stdout=stdout, stderr=stderr)
    pr.wait()
    stdout.seek(0)
    stderr.seek(0)
    return stdout.read(), stderr.read()

def start_ssh_server(ssh_user):
    # Generate password
    password, _ = execute_process(["/usr/bin/openssl", "rand", "-base64", "10"], internal_command=True, user=ssh_user)
    password = password.decode('utf8').strip()
    execute_process(["/usr/bin/bash", "-c", "echo '{}:{}' | chpasswd".format(ssh_user, password)],
                    internal_command=True, user=ssh_user)
    # generate the host keys
    execute_process(["/usr/bin/ssh-keygen", "-A"], internal_command=True, user=ssh_user)

    # remove /run/nologin if it exists
    if os.path.exists("/run/nologin"):
        os.unlink("/run/nologin")

    permit_root_login = "yes" if ssh_user == "root" else "no"

    # Start the ssh server
    execute_process(["/usr/sbin/sshd",
                    "-p", "22",
                    "-o", "PermitRootLogin={}".format(permit_root_login),
                    "-o", "PasswordAuthentication=yes", "-o", "StrictModes=no",
                    "-o", "ForceCommand=echo LOGIN: Good luck !; script -q .ssh_logs; cp .ssh_logs student/.ssh_logs; echo LOGOUT: Good bye!",
                    "-o", "AllowUsers={}".format(ssh_user)], internal_command=True, user=ssh_user)
    return ssh_user, password
    #When logging in, student is in a special interactive shell where everything is logged into a file.
    #When he exits this special shell, the log file is copied into the student directory and the ssh connection closes


def ssh_wait(ssh_user, timeout=None):
    """ Wait maximum 2 minutes for user ssh_user to connect.
    Wait for the user to leave. No timeout unless specified (the container has already a timeout anyway)"""
    connected_workers = 0
    attempts = 0
    while connected_workers == 0 and attempts < 120:  # wait max 2min for someone to connect
        time.sleep(1)
        stdout, stderr = execute_process(
            ["/bin/bash", "-c", "ps -f -C sshd | grep '{}@pts' | wc -l".format(ssh_user)], internal_command=True, user=ssh_user)
        connected_workers = int(stdout)
        attempts += 1
    attempts = 0
    if connected_workers != 0:  # If someone is connected, wait until no one remains
        while connected_workers != 0:
            if timeout is not None and attempts >= timeout:
                print("Timeout while user was still connected !")
                return 253  # timeout
            time.sleep(1)
            stdout, stderr = execute_process(
                ["/bin/bash", "-c", "ps -f -C sshd | grep '{}@pts' | wc -l".format(ssh_user)], internal_command=True, user=ssh_user)
            connected_workers = int(stdout)
            attempts += 1
        return 0  # The user connected and disconnected
    else:
        print("No one connected !")
        return 253  # timeout
