import struct
import os

"""
Various utilities for oblique
"""

__all__ = ["gen_session_id"]


def gen_session_id(id_container=set()) -> int:
    """
    Generate a random 4-byte session ID and ensures that it is not contained in the
    container provided. If no container is provided, a local one will be used.
    """
    i = None
    while i is None or i in id_container:
        i = struct.unpack(">L", os.urandom(4))[0]
    id_container.add(i)
    return i
