import asyncio
from oblique.bases import BaseServer, BaseListener
from oblique.commands import Command, compose


class ListenerTCP(BaseListener, asyncio.Protocol):
    """
    Listener protocol for oblique.
    Listeners will accept connections from endpoints, associate with a session ID,
    and tunnel over the main Oblique server/client connection.

    One ListenerTCP instance will be created for each incoming connection.
    """

    def __init__(self, server: BaseServer):
        """
        Construct a TCP listener
        :param server: the main Server from which the listener was spawned
        """
        super().__init__(server)
        self.transport = None
        self.peername = None
        self.session_id = self.server.gen_session_id()
        self.server.add_session(self.session_id, self)

    def connection_lost(self, exc: Exception) -> None:
        """
        Connection from the endpoint lost. Inform the client and delete the session ID

        :param exc: exception provided by asyncio
        :return: None
        """
        self.log.warning("Session {:08x} disconnected from {}:{}".format(self.session_id, *self.peername))
        self.server.del_session(self.session_id)
        self.server.transport.write(compose(Command.dead, self.session_id, None))
        self.transport.close()

    def connection_made(self, transport: asyncio.Transport) -> None:
        """
        A TCP connection was received from an endpoint

        :param transport: endpoint transport provided by asyncio
        :return: None
        """
        self.transport = transport
        self.peername = transport.get_extra_info("peername")
        self.server.transport.write(compose(Command.open, self.session_id, None))
        self.log.info("Connection Open: Session {:08x}: {}:{}".format(self.session_id, *self.peername))

    def data_received(self, data: bytes) -> None:
        """
        Data received from a listener. Forward it out the server's connection to the client
        along with the session ID
        :param data: data sent by the endpoint protocol
        :return: None
        """
        self.log.debug("Session {:08x} received {} bytes".format(self.session_id, len(data)))
        pkt = compose(Command.data, self.session_id, data)
        self.log.info("Sendng to {}:{}".format(*self.server.transport.get_extra_info("peername")))
        self.server.transport.write(pkt)

    def send(self, data: bytes) -> None:
        """
        TCP implementation of repeating data. Simply use the transport

        :param data: data to send
        :return: None
        """
        try:
            self.transport.write(data)
        except Exception as e:
            print(e)

    def close(self) -> None:
        self.log.info("Session {:08x} Closed".format(self.session_id))
        try:
            if self.transport.can_write_eof():
                self.transport.write_eof()
            self.transport.close()
        except Exception as e:
            print(e)