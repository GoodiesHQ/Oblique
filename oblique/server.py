import asyncio
import random
import struct
import sys

from asyncio.transports import Transport, DatagramTransport
from functools import partial

from oblique.bases import BaseServer
from oblique.commands import Command, Mode, parse, compose
from oblique.listener import ListenerTCP

"""
Oblique Server implementation

Oblique is a TCP protocol that runs over IPv4/IPv6.
"""

__all__ = ["Server", "create_server"]


class Server(BaseServer):
    def __init__(self, loop: asyncio.AbstractEventLoop=None):
        super().__init__(loop)

    def connection_lost(self, exc):
        print("[Server]", exc, file=sys.stderr)

    def connection_made(self, transport: Transport) -> None:
        """
        An oblique client has connected.

        :param transport: transport supplied by asyncio
        :return: None
        """
        print("[Server] Client connected from {}:{}".format(*transport.get_extra_info("peername")))
        self.transport = transport

    def data_received(self, data: bytes) -> None:
        """
        Data received from the client
        :param data: data supplied by asyncio
        :return: None
        """
        try:
            for (cmd, sid, data) in parse(data):
                if cmd == Command.dead:
                    self.del_session(sid)
                    return
                if cmd == Command.init:
                    if sid != 0:
                        print("[Server] Init SID is not zero", file=sys.stderr)
                        self.transport.write(compose(Command.invalid, 0, None))
                        self.transport.close()
                        return
                    mode = struct.unpack(">L", data[:4])[0]
                    if mode == Mode.tcp:
                        done = False
                        while not done:
                            port = random.randint(1025, 65535)
                            try:
                                def successful(_):
                                    msg = data[4:]
                                    print("[Server] TCP Listener created on port {}: {}".format(port, msg.decode()))
                                    self.transport.write(
                                        compose(Command.init,
                                                0,
                                                struct.pack(">L", mode) + b"Successfully created a listener.")
                                    )

                                fut = asyncio.ensure_future(
                                    self.loop.create_server(partial(ListenerTCP, self), host="", port=port)
                                )

                                fut.add_done_callback(successful)
                            except OSError:
                                pass
                            else:
                                done = True

                if cmd == Command.data:
                    if sid not in self.sessions:
                        self.transport.write(compose(Command.invalid, sid, None))
                        return
                    self.sessions[sid].send(data)

        except ValueError as e:
            print("[Server] Error Received: {}".format(e), file=sys.stderr)
            self.transport.write(compose(Command.invalid, 0, None))
            self.transport.close()
            return


def create_server(host: str="",
                  port: int=8000,
                  loop: asyncio.AbstractEventLoop=None):
    """
    Creates server sockets bound to a specific address:port supporting the protocols provided

    :param port: local port to bind
    :param host: local host to bind
    :param loop: asyncio event loop
    :return:
    """
    loop = loop or asyncio.get_event_loop()
    return loop.create_server(Server, host=host, port=port, reuse_address=True)
