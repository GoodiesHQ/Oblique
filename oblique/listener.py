import asyncio
import sys
from oblique.bases import BaseServer, BaseListener
from oblique.commands import Command, compose
from oblique.utils import gen_session_id


class ListenerTCP(BaseListener, asyncio.Protocol):
    """
    Listener protocol for oblique.
    Listeners will accept connections from endpoints, associate with a session ID,
    and tunnel over the main Oblique server/client connection.
    """

    def __init__(self, server: BaseServer):
        super().__init__(server)
        self.transport = None
        self.session_id = gen_session_id()
        self.server.add_session(self.session_id, self)

    def connection_lost(self, exc: Exception) -> None:
        """
        Connection from the endpoint lost. Inform the client and delete the session ID

        :param exc: exception provided by asyncio
        :return: None
        """
        print("[Listener] Connection Lost. Dead Session: {:08x}".format(self.session_id), file=sys.stderr)
        self.server.del_session(self.session_id)
        self.server.transport.write(compose(Command.dead, self.session_id, None))
        self.transport.close()

    def connection_made(self, transport: asyncio.Transport) -> None:
        """
        A TCP connection was received from an endpoint

        :param transport: endpoint transport provided by asyncio
        :return: None
        """
        print("[Listener] Connection received. Session ID: {:x}".format(self.session_id))
        self.transport = transport
        self.server.transport.write(compose(Command.open, self.session_id, None))

    def data_received(self, data: bytes) -> None:
        """
        Data received from a listener. Forward it out the server's connection to the client
        along with the session ID
        :param data: data sent by the endpoint protocol
        :return: None
        """
        pkt = compose(Command.data, self.session_id, data)
        self.server.transport.write(pkt)

    def send(self, data: bytes) -> None:
        """
        TCP implementation of repeating data. Simply use the transport

        :param data: data to send
        :return: None
        """
        self.transport.write(data)
