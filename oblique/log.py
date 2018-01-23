import logging
from logging.handlers import RotatingFileHandler
from logging import StreamHandler, Formatter
from oblique.utils import Singleton

__all__ = ["LogHandler", "make_logger"]


class LogHandler(metaclass=Singleton):
    """
    Singleton that holds the same RotatingFileHandler instance
    """
    _file = None
    _stream = None
    _fmt = None

    @property
    def fmt(self) -> Formatter:
        if self._fmt is None:
            self._fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        return self._fmt

    @property
    def file(self) -> RotatingFileHandler:
        """
        Creates the handler if none exists.

        :return: the log file handler
        """
        if self._file is None:
            self._file = RotatingFileHandler("oblique.log", maxBytes=10*1024*1024, backupCount=20)
            self._file.setFormatter(self.fmt)
        return self._file

    @property
    def stream(self) -> StreamHandler:
        """
        Creates the stream handler if none eists.

        :return: the log stream handler
        """
        if self._stream is None:
            self._stream = StreamHandler()
            self._stream.setFormatter(self.fmt)
        return self._stream


def make_logger(name: str="oblique", level=logging.DEBUG) -> logging.Logger:
    """
    Creates a logger based on the provided name

    :param name: the name appended to the logger.
    :param level: the logging level of the new logger (will overwrite existing loggers with the same name)
    :return the new Logger instance
    """
    log = logging.getLogger(name.lower())
    log.setLevel(level)
    han = LogHandler()
    log.addHandler(han.file)
    log.addHandler(han.stream)
    return log
