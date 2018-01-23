import asyncio
import os
import struct
import threading
from abc import ABC, abstractmethod, abstractproperty
from contextlib import suppress
from logging import Logger
from typing import Union
from oblique.log import make_logger

__all__ = ["BaseLoggable", "BaseSender", "BaseServer", "BaseListener", "BaseClient", "BaseRepeater"]


class BaseLoggable(object):
    """
    Base Loggable class. Anything that should implement logging via self.log()
    """
    _log = None

    @property
    def log(self) -> Logger:
        """
        Create a logger if none exists in the current instance. All loggers write to the same file, but the names will
        differ based on the class.
        :return: Logger
        """
        if self._log is None:
            self._log = make_logger(self.__class__.__name__)
        return self._log


class BaseSender(ABC):
    """
    Base sender class. Anything that implements the .send() method.
    """
    @abstractmethod
    def send(self, data: bytes) -> None:
        """
        Send the data according to the classes own way of sending data.
        :return: None
        """


class BaseSessionTracking(object):
    """
    Subclasses will be allowed to track sessions
    """
    def __init__(self):
        self.id_container = set()
        self.lock = threading.Lock()
        self.sessions = dict()

    def gen_session_id(self) -> int:
        """
        Generate a random 4-byte session ID and ensures that it is not contained in the instance's id_container
        """
        i = None
        while i is None or i in self.id_container:
            i = struct.unpack(">L", os.urandom(4))[0]
        self.id_container.add(i)
        return i

    def add_session(self, session_id: int, sender: Union[BaseSender, None]) -> None:
        """
        Register a session with a server so it knows which connection to proxy

        :param session_id: session id
        :param sender: the listener
        :return: None
        """
        with self.lock:
            self.sessions[session_id] = sender

    def get_session(self, session_id: int):
        """
        Retrieves a transport from as Session ID
        :param session_id: session ID
        :return: the listener object or None if session ID is not found
        """
        with self.lock:
            return self.sessions.get(session_id, None)

    def del_session(self, session_id: int) -> None:
        """
        Unregisters a session with a server
        :param session_id: session id
        :return: None
        """
        with suppress(KeyError):
            del self.sessions[session_id]


class BaseComponent(asyncio.Protocol, BaseSessionTracking, BaseLoggable):
    """
    Common base class for Oblique Servers and Clients.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop=None):
        """
        Implements everything the main Client/Server components share

        :param loop: asyncio event loop
        """
        super().__init__()
        self.loop = loop or asyncio.get_event_loop()
        self.transport = None


class BaseServer(BaseComponent):
    """
    Base server class. Handles connections from Oblique clients.
    """


class BaseListener(BaseSender, BaseLoggable):
    """
    Base listener class. Stores the parent server.
    """
    def __init__(self, server):
        super().__init__()
        self.server = server

    @abstractmethod
    def send(self, data: bytes):
        """Implemented by each listener."""


class BaseClient(BaseComponent):
    pass


class BaseRepeater(BaseSender, BaseLoggable):
    """
    Base repeater class. Stores the parent client.
    """
    def __init__(self, client):
        super().__init__()
        self.client = client

    @abstractmethod
    def send(self, data: bytes):
        """Implemented by each repeater."""
