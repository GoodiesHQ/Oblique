import asyncio
import random
import struct
import sys

from asyncio.transports import Transport, DatagramTransport
from functools import partial

from oblique.bases import BaseServer, BaseListener
from oblique.commands import Command, Mode, parse, compose
from oblique.listener import ListenerTCP
from oblique.log import make_logger

"""
Oblique Server implementation

Oblique is a TCP protocol that runs over IPv4/IPv6.
"""

__all__ = ["Server", "create_server"]


class Server(BaseServer):
    def __init__(self, loop: asyncio.AbstractEventLoop=None):
        super().__init__(loop)
        self.log.debug("instantiated")
        self.peername = None
        self.listener = None

    def connection_lost(self, exc):
        self.log.error("Connection Lost from client {}:{}".format(*self.transport.get_extra_info("peername")))

    def connection_made(self, transport: Transport) -> None:
        """
        An oblique client has connected.

        :param transport: transport supplied by asyncio
        :return: None
        """
        self.peername = transport.get_extra_info("peername")
        self.log.info("Client connected from {}:{}".format(*self.peername))
        self.transport = transport

    def data_received(self, data: bytes) -> None:
        """
        Data received from the client
        :param data: data supplied by asyncio
        :return: None
        """
        self.log.debug("{} bytes received".format(len(data)))
        try:
            for (cmd, sid, data) in parse(data):
                if cmd == Command.dead:
                    self.log.warning("Session {:08x} dead.".format(sid))
                    sess = self.get_session(sid)
                    if sess:
                        sess.close()
                        self.del_session(sid)
                    return

                if cmd == Command.init:
                    self.log.debug("INIT received from Client {}:{}".format(*self.peername))
                    if sid != 0:
                        self.transport.write(compose(Command.invalid, 0, None))
                        self.transport.close()
                        return

                    mode = struct.unpack(">L", data[:4])[0]
                    if mode == Mode.tcp:
                        done = False
                        while not done:
                            port = random.randint(1025, 65535)
                            try:
                                def successful(listener: ListenerTCP):
                                    self.listener = listener
                                    msg = data[4:]
                                    self.log.info("Created TCP Listener on port {}".format(port))
                                    self.log.info("Client INIT: {}".format(msg.decode()))
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
                    self.log.info("Received {} bytes on session {:08x}".format(len(data), sid))
                    if sid not in self.sessions:
                        self.transport.write(compose(Command.invalid, sid, None))
                        return
                    session = self.get_session(sid)
                    if session:
                        print("Server ID", id(self.sessions))
                        session.send(data)

        except ValueError as e:
            self.log.critical("Error: {}".format(e))
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
    server = loop.create_server(Server, host=host, port=port, reuse_address=True)
    log = make_logger()
    log.info("Server Created on {}:{}".format(host, port))
    return server
