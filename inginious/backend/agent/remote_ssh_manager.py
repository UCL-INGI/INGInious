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
""" Agent, managing docker (remote version) """
import logging

import threading
import socket
import select

class ManageSSHConnection(threading.Thread):
    """Manages a single connection to a remote ssh"""

    def __init__(self, conn, addr, remote_addr, remote_port):
        super(ManageSSHConnection, self).__init__()
        self.daemon = True
        self._conn = conn
        self._addr = addr
        self._remote_addr = remote_addr
        self._remote_port = remote_port
        self.start()

    def run(self):
        client = socket.create_connection((self._remote_addr, self._remote_port))
        try:
            while True:
                read, write, exception = select.select([self._conn, client], [], [self._conn, client])
                if len(exception) != 0:
                    break
                if self._conn in read:
                    data = self._conn.recv(1024)
                    if data is None or len(data) == 0:
                        break
                    client.send(data)
                elif client in read:
                    data = client.recv(1024)
                    if data is None or len(data) == 0:
                        break
                    self._conn.send(data)
        except:
            pass
        finally:
            client.close()
            self._conn.close()

class RemoteSSHManager(threading.Thread):
    """ Manages connections to the different debug ssh containers running """

    logger = logging.getLogger("agent.remotessh")

    def __init__(self, port_or_filename):
        super(RemoteSSHManager, self).__init__()
        self.daemon = True
        self._port_or_filename = port_or_filename
        self._open_connections = {}
        self.start()

    def add_open_connection(self, conn_id, remote_addr, remote_port):
        """ Add a possible distant ssh server to the manager """
        self._open_connections[conn_id] = (remote_addr, remote_port)

    def del_connection(self, conn_id):
        """ Remove the possibility to connect to a distant server """
        try:
            del self._open_connections[conn_id]
        except:
            pass

    def run(self):
        if isinstance(self._port_or_filename, basestring):
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(self._port_or_filename)
        else:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(('0.0.0.0', self._port_or_filename))
        server.listen(1)
        while True:
            try:
                conn, addr = server.accept()
                conn_id = ""
                while "\n" not in conn_id:
                    conn_id += conn.recv(64)
                self.logger.debug("Received connection. Conn_id: %s", conn_id.strip())
                conn_data = self._open_connections.get(conn_id.strip())
                if conn_data is None:
                    conn.send("ko\n")
                else:
                    conn.send("ok\n")
                    ManageSSHConnection(conn, addr, conn_data[0], conn_data[1])
            except:
                pass
