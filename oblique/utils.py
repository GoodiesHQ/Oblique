"""
Various utilities for oblique
"""

__all__ = ["Singleton"]


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


