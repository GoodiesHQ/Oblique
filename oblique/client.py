import asyncio
import struct
import sys
from collections import defaultdict
from functools import partial
from oblique.commands import Command, Mode, compose, parse
from oblique.bases import BaseClient
from oblique.repeater import RepeaterTCP

__all__ = ["Client", "create_client"]


class Client(BaseClient):
    transport = None

    def __init__(self, host: str, port: int, mode: Mode, loop: asyncio.AbstractEventLoop=None):
        self.host = host
        self.port = port
        self.mode = mode
        self.buffers = defaultdict(list)
        super().__init__(loop=loop)

    def try_send(self, session_id: int, data: bytes=None, retries: int=3, delay: int=100):
        """
        Attempt to send data through a repeater. If no session exists, connection may not have fully opened.
        Retry (3 times by default).

        :param session_id: the repeater session ID
        :param data: data
        :param retries: number of retries to attempt
        :param delay: delay, in milliseconds, between attempts
        :return:
        """
        if retries == 0:
            del self.buffers[session_id]
            self.del_session(session_id)
            return

        if data is not None:
            self.buffers[session_id].append(data)

        repeater = self.get_session(session_id)
        if repeater is None:
            self.loop.call_later(delay, self.try_send, session_id, None, retries-1)
            return

        for buf in self.buffers[session_id]:
            try:
                repeater.send(buf)
            except Exception as e:
                print("[Repeater] {}".format(e), file=sys.stderr)

        self.buffers[session_id].clear()

    def connection_made(self, transport):
        """
        Established a connection to the Oblique server.
        :param transport:
        :return:
        """
        self.transport = transport
        info = "Forwarding to {}:{}".format(self.host, self.port)
        print("Client ID", id(self.sessions))
        self.transport.write(compose(Command.init, 0, struct.pack(">L", self.mode) + info.encode()))

    def data_received(self, data: bytes):
        try:
            for(cmd, sid, data) in parse(data):
                if cmd == Command.init:
                    msg = data[4:]
                    if msg:
                        print("[Client] Init Message Received: {}".format(msg.decode()))

                if cmd == Command.open:
                    if self.mode == Mode.tcp:
                        asyncio.ensure_future(
                            self.loop.create_connection(partial(RepeaterTCP, sid, self), self.host, self.port)
                        )

                if cmd == Command.data:
                    self.try_send(sid, data)
        except ValueError as e:
            print(e)
            self.transport.close()
            return



def create_client(dest_host: str, dest_port: int,
                  server_host: str, server_port: int=8000,
                  mode: Mode=Mode.tcp,
                  loop: asyncio.AbstractEventLoop=None):
    loop = loop or asyncio.get_event_loop()
    return loop.create_connection(partial(Client, dest_host, dest_port, mode, loop), server_host, server_port)
