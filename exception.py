#!/usr/bin/python

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
