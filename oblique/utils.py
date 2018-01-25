import struct
import os

"""
Various utilities for oblique
"""

__all__ = ["Singleton"]


def gen_unique_id(id_container: set=set()) -> int:
    """
    Generates a unique ID that is not in the provided container. If no container is provided, a global one is used.
    :param id_container:
    :return:
    """
    i = None
    while i is None or i in id_container:
        i = struct.unpack(">L", os.urandom(4))[0]
    id_container.add(i)
    return i


class Singleton(type):
    """
    A simple singleton metaclass implementation
    """
    _inst = {}

    def __call__(cls, *args, **kwargs):
        """
        Return the instance of the class `cls`. Create it with args and kwargs if it doesn't already exist.

        :param args: args
        :param kwargs: kwargs
        :return: the instance of `cls`
        """
        if cls not in cls._inst:
            cls._inst[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._inst[cls]


