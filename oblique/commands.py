from typing import Tuple, Union, List
import enum
import struct

"""
Oblique command definitions, parsing, and handling
"""

__all__ = ["Command", "Mode", "compose", "parse"]

MAGIC_HEADER = 0xBACCAA73
HEADER_LEN = sum([
    4,  # Magic header
    1,  # Command
    4,  # Session ID
    4,  # length
    # arbitrary data
])


class Mode(enum.IntEnum):
    """
    3 modes:
        MGMT - connection is meant for the management server (dynamically deploys Oblique connections)
    """
    mgmt = 0
    tcp = 1
    udp = 2


class Command(enum.IntEnum):
    init = 0x01     # Client initialization packet sent to the server
    open = 0x02     # Server packet sent to the client to open a connection
    data = 0x03     # A data packet containing the data to forward
    dead = 0x04     # A connection died
    beat = 0xAA
    invalid = 0xF0  # The data received was invalid

    @staticmethod
    def valid(cmd: int) -> bool:
        return cmd in {
            Command.init,
            Command.open,
            Command.data,
            Command.dead,
            Command.beat,
            Command.invalid,
        }


def compose(command: Command, session_id: int, data: Union[bytes, None]):
    """
    Compose an oblique command packet

    :param command: a member of the Command enum
    :param session_id: the session ID for the connection
    :param data: the data to be sent
    :return: bytes
    """
    data = data or b""
    return struct.pack(">LBLL", MAGIC_HEADER, command, session_id, len(data)) + data


def parse_single(data: bytes) -> Tuple[int, int, bytes, bytes]:
    """
    Parse the input data and return the first received command, the associated session ID, and additional data.
    If any extra data is provided, it is returned and SHOULD be another command (multiple commands sent in the same
    stream). If not, exceptions are raised.

    :param data: raw data to parse
    :return: the command, session ID, and additional data provided (may be empty, but always bytes)
    """

    datalen = len(data)
    if datalen < HEADER_LEN:
        raise ValueError("Data is too small")

    (magic_header, cmd, sid, length) = struct.unpack(">LBLL", data[:HEADER_LEN])

    if magic_header != MAGIC_HEADER:
        raise ValueError("Invalid header")

    if (datalen - HEADER_LEN) < length:
        raise ValueError("Invalid length ({}, but expected {})".format(datalen - HEADER_LEN, length))

    if not Command.valid(cmd):
        raise ValueError("Invalid command")

    if cmd == Command.init:
        if length < 4:
            raise ValueError("Invalid Init Length")

    return cmd, sid, data[HEADER_LEN:HEADER_LEN+length], data[HEADER_LEN+length:]


def parse(data: bytes) -> Tuple[int, int, bytes]:
    extra = data
    while extra != b"":
        cmd, sid, data, extra = parse_single(extra)
        yield cmd, sid, data
