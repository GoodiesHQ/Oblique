import asyncio
import threading
from abc import ABC, abstractmethod
from contextlib import suppress
from typing import Union

__all__ = ["BaseSender", "BaseServer", "BaseListener", "BaseClient", "BaseRepeater"]


class BaseSender(ABC):
    @abstractmethod
    def send(self, data: bytes) -> None:
        """
        Send the data according to the classes own way of sending data.
        :return: None
        """


class BaseComponent(asyncio.Protocol):
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
        self.sessions = dict()
        self.lock = threading.Lock()

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


class BaseServer(BaseComponent):
    pass


class BaseListener(BaseSender):
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


class BaseRepeater(BaseSender):
    """
    Base repeater class. Stores the parent client.
    """
    def __init__(self, client):
        super().__init__()
        self.client = client

    @abstractmethod
    def send(self, data: bytes):
        """Implemented by each listener."""
