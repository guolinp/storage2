#!/usr/bin/python

import logging


class Logger(object):
    _logger = None

    @classmethod
    def get_logger(cls, filename, console=False):
        if cls._logger is not None:
            return cls._logger

        logger = logging.getLogger('Logger')
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(asctime)s [%(filename)s,%(lineno)d] - %(name)s - %(levelname)s - %(message)s')

        file_handle = logging.FileHandler(filename)
        file_handle.setLevel(logging.DEBUG)
        file_handle.setFormatter(formatter)
        logger.addHandler(file_handle)

        if console:
            console_handle = logging.StreamHandler()
            console_handle.setLevel(logging.DEBUG)
            console_handle.setFormatter(formatter)
            logger.addHandler(console_handle)

        cls._logger = logger

        return cls._logger
