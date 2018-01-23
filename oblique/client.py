import asyncio
import struct
from contextlib import suppress
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

    def try_send(self, session_id: int, data: bytes=None, retries: int=3, delay: float=0.25):
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
            self.log.info("Max Retries. Session {:08x} unavailable.".format(session_id))
            del self.buffers[session_id]
            self.del_session(session_id)
            self.transport.write(compose(Command.dead, session_id, None))
            return

        if data is not None:
            self.buffers[session_id].append(data)

        repeater = self.get_session(session_id)
        if repeater is None:
            self.log.info("Retrying Session {:08x}...".format(session_id))
            self.loop.call_later(delay, self.try_send, session_id, None, retries-1)
            return

        for buf in self.buffers[session_id]:
            try:
                repeater.send(buf)
            except Exception as e:
                self.log.error(e)

        self.buffers[session_id].clear()

    def connection_made(self, transport):
        """
        Established a connection to the Oblique server.
        :param transport:
        :return:
        """
        self.transport = transport
        info = "Forwarding to {}:{}".format(self.host, self.port)
        self.transport.write(compose(Command.init, 0, struct.pack(">L", self.mode) + info.encode()))

    def data_received(self, data: bytes):
        try:
            for(cmd, sid, data) in parse(data):
                if cmd == Command.init:
                    msg = data[4:]
                    if msg:
                        self.log.info("INIT Message: {}".format(msg.decode()))

                if cmd == Command.dead:
                    self.log.warning("Session {:08x} dead.".format(sid))
                    sess = self.get_session(sid)
                    if sess is not None:
                        sess.close()

                if cmd == Command.open:
                    if self.mode == Mode.tcp:
                        def tcp_open(conn):
                            if conn.exception() is not None:
                                with suppress(KeyError):
                                    del self.buffers[sid]
                                self.del_session(sid)
                                self.transport.write(compose(Command.dead, sid, None))
                        fut = asyncio.ensure_future(
                            self.loop.create_connection(partial(RepeaterTCP, sid, self), self.host, self.port)
                        )
                        fut.add_done_callback(tcp_open)

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
