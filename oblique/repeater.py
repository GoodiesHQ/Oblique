import asyncio
from oblique.commands import Command, compose
from oblique.bases import BaseRepeater


class RepeaterTCP(BaseRepeater, asyncio.Protocol):
    def __init__(self, session_id, client):
        super().__init__(client)
        self.session_id = session_id
        self.transport = None
        self.peername = None
        self.log.debug("Created Repeater for session ID {:08x}".format(session_id))

    def connection_made(self, transport: asyncio.Transport) -> None:
        """
        Connection made from the repeater to the destination host/port

        :param transport: transport provided by asyncio
        :return:
        """
        self.transport = transport
        self.peername = transport.get_extra_info("peername")
        self.log.info("Session {:08x} made to {}:{}".format(self.session_id, *self.peername))
        self.client.add_session(self.session_id, self)
        self.client.transport.write(compose(Command.open, self.session_id, None))

    def connection_lost(self, exc):
        self.log.warning("Session {:08x} list to {}:{}".format(self.session_id, *self.peername))
        self.client.transport.write(compose(Command.dead, self.session_id, None))
        self.client.del_session(self.session_id)
        self.transport.close()

    def data_received(self, data):
        self.log.debug("Session {:08x} received {} bytes".format(self.session_id, len(data)))
        pkt = compose(Command.data, self.session_id, data)
        self.client.transport.write(pkt)

    def send(self, data: bytes) -> None:
        """
        Send data to the destination host:port

        :param data: data to send
        :return: None
        """
        self.transport.write(data)

    def close(self) -> None:
        """
        Close the connection
        :return: None
        """
        try:
            if self.transport.can_write_eof():
                self.transport.write_eof()
            self.transport.close()
        except Exception as e:
            print(e)
