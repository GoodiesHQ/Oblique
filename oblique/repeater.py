import asyncio
from oblique.commands import Command, compose
from oblique.bases import BaseRepeater


class RepeaterTCP(BaseRepeater, asyncio.Protocol):
    def __init__(self, session_id, client):
        super().__init__(client)
        self.session_id = session_id
        self.transport = None

    def connection_made(self, transport):
        """Connection made by the client"""
        print("[Repeater] Connection made to endpoint")
        self.transport = transport
        self.client.add_session(self.session_id, self)
        self.client.transport.write(compose(Command.open, self.session_id, None))

    def data_received(self, data):
        pkt = compose(Command.data, self.session_id, data)
        self.client.transport.write(pkt)

    def send(self, data: bytes):
        self.transport.write(data)

