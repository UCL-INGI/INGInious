# -*- coding: utf-8 -*-
# Copyright (c) 2005-2013
#  Tomer Filiba (tomerfiliba@gmail.com)
#  Copyrights of patches are held by their respective submitters
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
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
""" Custom RPyC Server that uses UNIX Sockets """

import errno
import logging
import os
import socket
import sys
import threading

from rpyc.core import SocketStream, Channel, Connection
from rpyc.lib.compat import get_exc_errno
from rpyc.utils.authenticators import AuthenticationError


class UnixSocketServer(object):
    """A (simple) RPyC server that uses UNIX Sockets

    :param service: the :class:`service <service.Service>` to expose
    :param socket_path: path to the unix socket to use
    :param backlog: the socket's backlog (passed to ``listen()``)
    :param reuse_addr: whether or not to create the socket with the ``SO_REUSEADDR`` option set.
    :param authenticator: the :ref:`api-authenticators` to use. If ``None``, no authentication
                          is performed.
    :param protocol_config: the :data:`configuration dictionary <rpyc.core.protocol.DEFAULT_CONFIG>`
                            that is passed to the RPyC connection
    :param logger: the ``logger`` to use (of the built-in ``logging`` module). If ``None``, a
                   default logger will be created.
    :param listener_timeout: the timeout of the listener socket; set to ``None`` to disable (e.g.
                             on embedded platforms with limited battery)
    """

    def __init__(self, service, socket_path,
                 backlog=10, authenticator=None, protocol_config=None,
                 logger=None, listener_timeout=0.5):
        protocol_config = protocol_config or []
        self.active = False
        self._closed = False
        self.service = service
        self.authenticator = authenticator
        self.backlog = backlog
        self.protocol_config = protocol_config
        self.clients = set()

        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        self.listener.bind(socket_path)
        os.chmod(socket_path, 0o777)
        self.listener.settimeout(listener_timeout)

        if logger is None:
            logger = logging.getLogger("%s" % (self.service.get_service_name()))
        self.logger = logger
        if "logger" not in self.protocol_config:
            self.protocol_config["logger"] = self.logger

    def close(self):
        """Closes (terminates) the server and all of its clients. If applicable,
        also unregisters from the registry server"""
        if self._closed:
            return
        self._closed = True
        self.active = False
        try:
            self.listener.shutdown(socket.SHUT_RDWR)
        except (EnvironmentError, socket.error):
            pass
        self.listener.close()
        self.logger.info("listener closed")
        for c in set(self.clients):
            try:
                c.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            c.close()
        self.clients.clear()

    def fileno(self):
        """returns the listener socket's file descriptor"""
        return self.listener.fileno()

    def accept(self):
        """accepts an incoming socket connection (blocking)"""
        while self.active:
            try:
                sock, _ = self.listener.accept()
            except socket.timeout:
                pass
            except socket.error:
                ex = sys.exc_info()[1]
                if get_exc_errno(ex) == errno.EINTR:
                    pass
                else:
                    raise EOFError()
            else:
                break

        if not self.active:
            return

        sock.setblocking(True)
        self.clients.add(sock)
        self._accept_method(sock)

    def _accept_method(self, sock):
        """this method should start a thread, fork a child process, or
        anything else in order to serve the client. once the mechanism has
        been created, it should invoke _authenticate_and_serve_client with
        `sock` as the argument"""
        t = threading.Thread(target=self._authenticate_and_serve_client, args=(sock,))
        t.setDaemon(True)
        t.start()

    def _authenticate_and_serve_client(self, sock):
        try:
            if self.authenticator:
                addrinfo = sock.getpeername()
                h = addrinfo[0]
                p = addrinfo[1]
                try:
                    sock2, credentials = self.authenticator(sock)
                except AuthenticationError:
                    self.logger.info("[%s]:%s failed to authenticate, rejecting connection", h, p)
                    return
                else:
                    self.logger.info("[%s]:%s authenticated successfully", h, p)
            else:
                credentials = None
                sock2 = sock
            try:
                self._serve_client(sock2, credentials)
            except Exception:
                self.logger.exception("client connection terminated abruptly")
                raise
        finally:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            sock.close()
            self.clients.discard(sock)

    def _serve_client(self, sock, credentials):
        addrinfo = sock.getpeername()
        try:
            config = dict(self.protocol_config, credentials=credentials,
                          endpoints=(sock.getsockname(), addrinfo), logger=self.logger)
            conn = Connection(self.service, Channel(SocketStream(sock)),
                              config=config)
            conn.serve_all()
        finally:
            pass

    def start(self):
        """Starts the server (blocking). Use :meth:`close` to stop"""
        self.listener.listen(self.backlog)
        self.active = True
        try:
            while self.active:
                self.accept()
        except EOFError:
            pass  # server closed by another thread
        except KeyboardInterrupt:
            print("")
            self.logger.warn("keyboard interrupt!")
        finally:
            self.logger.info("server has terminated")
            self.close()
