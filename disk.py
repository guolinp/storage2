#!/usr/bin/python

import os
import mmap
import contextlib

from error import *
from device import Device


class Disk(Device):

    '''disk base class'''
    pass


class MemoryDisk(Disk):

    '''a disk based on memory'''

    def __init__(self, name):
        raise FunctionalNotImplementError('TODO')


class NetworkDisk(Disk):

    '''a disk based on the network resource'''

    def __init__(self, name):
        raise FunctionalNotImplementError('TODO')


class FileDisk(Disk):

    '''a disk based on a local file'''

    def __init__(self, name, pathname):
        super(FileDisk, self).__init__(name)
        self._pathname = pathname

    @property
    def size(self):
        if self._size == 0:
            try:
                self._size = os.path.getsize(self._pathname)
            except Exception as e:
                raise DeviceAccessError(str(e))
        return self._size

    @property
    def info(self):
        return 'pathname: %s' % (self._pathname)

    def read(self, offset, length):
        data = None
        self.logger.debug('start read on %s, offset %d, length %d' %
                          (self.name, offset, length))

        if not self.is_valid_range(offset, length):
            self.logger.error(
                'Invalid argument: offset %d, length %d' % (offset, length))
            return err_invalid_argument, data

        try:
            fileno = os.open(self._pathname, os.O_RDWR)
            with contextlib.closing(mmap.mmap(fileno, 0)) as m:
                m.seek(offset)
                data = m.read(length)
            os.close(fileno)
        except Exception as e:
            raise DeviceAccessError(str(e))

        if data is None or len(data) != length:
            self.logger.error('data length %d, expected length %d' %
                              (0 if data is None else len(data), length))
            return err_read_data_fail, data
        else:
            return err_success, data

    def write(self, data, offset):
        self.logger.debug('start write on %s: offset %d, length %d' %
                          (self.name, offset, 0 if data is None else len(data)))
        if data is None:
            self.logger.error('Invalid argument: data is none')
            return err_invalid_argument

        if self.is_valid_range(offset, len(data)):
            try:
                fileno = os.open(self._pathname, os.O_RDWR)
                with contextlib.closing(mmap.mmap(fileno, 0)) as m:
                    m.seek(offset)
                    m.write(data)
                os.close(fileno)
            except Exception as e:
                raise DeviceAccessError(str(e))

        return err_success
