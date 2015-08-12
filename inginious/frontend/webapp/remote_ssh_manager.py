# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" Manages calls to remote ssh servers """
import threading
import socket
import select
from bson import ObjectId


class SocketRelay(threading.Thread):
    """Manages a single connection to a remote ssh"""

    def __init__(self, sock1, sock2):
        super(SocketRelay, self).__init__()
        self.daemon = True
        self._sock1 = sock1
        self._sock2 = sock2

    def run(self):
        try:
            while True:
                read, write, exception = select.select([self._sock1, self._sock2], [], [self._sock1, self._sock2])
                if len(exception) != 0:
                    break
                if self._sock1 in read:
                    data = self._sock1.recv(1024)
                    if data is None or len(data) == 0:
                        break
                    self._sock2.send(data)
                elif self._sock2 in read:
                    data = self._sock2.recv(1024)
                    if data is None or len(data) == 0:
                        break
                    self._sock1.send(data)
        except:
            pass
        finally:
            self._sock1.close()
            self._sock2.close()


class RemoteSSHManager(threading.Thread):
    """ Manages connections to the different debug ssh containers running """

    def __init__(self, host, port, database, job_manager):
        super(RemoteSSHManager, self).__init__()
        self.daemon = True
        self._host = host
        self._port = port
        self._database = database
        self._job_manager = job_manager
        self._stopped = True

    def get_url(self):
        """ Returns a string host:ip pointing to the open socket for the remote debugging """
        return str(self._host)+":"+str(self._port)

    def start(self):
        self._stopped = False
        super(RemoteSSHManager, self).start()

    def stop(self):
        """ Stop the server """
        self._stopped = True

    def is_active(self):
        """ Returns True if remote debugging is activated """
        return not self._stopped

    def run(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server.bind((self._host, self._port))
            server.listen(1)
            server.settimeout(1)
            while not self._stopped:
                try:
                    conn, _ = server.accept()
                    conn.setblocking(1)
                except KeyboardInterrupt:
                    raise
                except:
                    continue

                try:
                    submission_id = ""
                    while "\n" not in submission_id:
                        submission_id += conn.recv(64)
                    submission_id = submission_id.strip()

                    submission = self._database.submissions.find_one({"_id": ObjectId(submission_id)})
                    if submission is None or "ssh_conn_id" in submission:
                        raise Exception("Cannot get submission")

                    sock = self._job_manager.get_socket_to_debug_ssh(submission["ssh_internal_conn_id"])
                    if sock is None:
                        raise Exception("Cannot get socket")

                    conn.send("ok\n")
                    SocketRelay(conn, sock).start()
                except KeyboardInterrupt:
                    conn.close()
                    raise
                except:
                    conn.send("ko\n")
                    conn.close()
        except:
            server.close()
            raise
