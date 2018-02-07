#!/usr/bin/python

# Error code defines

err_success = 0
err_invalid_argument = 1024
err_out_of_range = 1025
err_read_data_fail = 1025
err_write_data_fail = 1027

# Error helper functions


def is_success(err):
    return err == err_success


# Exceptions
class StorgeError(Exception):

    def __init__(self, value='A storage error'):
        self._value = value

    def __str__(self):
        return 'Error value: %s' % self._value


class InvalidArgumentError(StorgeError):
    pass


class DeviceNotFoundError(StorgeError):
    pass


class DeviceNotAvailableError(StorgeError):
    pass


class DeviceAccessError(StorgeError):
    pass


class FunctionalNotImplementError(StorgeError):
    pass
