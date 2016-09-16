import asyncio


class SimpleEchoProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        """
        Called when a connection is made.
        The argument is the transport representing the pipe connection.
        To receive data, wait for data_received() calls.
        When the connection is closed, connection_lost() is called.
        """
        print("Connection received!")
        self.transport = transport

    def data_received(self, data):
        """
        Called when some data is received.
        The argument is a bytes object.
        """
        print(data)
        self.transport.write(b'echo:')
        self.transport.write(data)

    def connection_lost(self, exc):
        """
        Called when the connection is lost or closed.
        The argument is an exception object or None (the latter
        meaning a regular EOF is received or the connection was
        aborted or closed).
        """
        print("Connection lost! Closing server...")
        server.close()


loop = asyncio.get_event_loop()
server = loop.run_until_complete(loop.create_server(SimpleEchoProtocol, 'localhost', 2222))
loop.run_until_complete(server.wait_closed())