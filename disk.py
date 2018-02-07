#!/usr/bin/python

import os
import mmap
import contextlib

from error import *
from exception import *
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
    @property
    def size(self):
        if self._size > 0:
            return self._size
        try:
            self._size = os.stat(self._name).st_size
        except Exception as e:
            raise DeviceAccessError(str(e))

        return self._size


    def read(self, offset, length):
        self.logger.debug('start read on %s, offset %d, length %d' % (self._name, offset, length))
        if not self._is_valid_range(offset, length):
            self.logger.error('Invalid argument: offset %d, length %d' % (offset, length))
            return err_invalid_argument

        data = None
        try:
            fileno = os.open(self._name, os.O_RDWR)
            with contextlib.closing(mmap.mmap(fileno, 0)) as m:
                m.seek(offset)
                data = m.read(length)
            os.close(fileno)
        except Exception as e:
            raise DeviceAccessError(str(e))

        if data is None or len(data) != length:
            self.logger.error('data length %d, expected length %d' % (len(data), 0 if data is None else len(data)))
            return err_read_data_fail, data
        else:
            return err_success, data


    def write(self, data, offset):
        self.logger.debug('start write on %s: offset %d, length %d' % (self._name, offset, 0 if data is None else len(data)))
        if data is None:
            self.logger.error('Invalid argument: data is none')
            return err_invalid_argument

        if self._is_valid_range(offset, len(data)):
            try:
                fileno = os.open(self._name, os.O_RDWR)
                with contextlib.closing(mmap.mmap(fileno, 0)) as m:
                    m.seek(offset)
                    m.write(data)
                os.close(fileno)
            except Exception as e:
                raise DeviceAccessError(str(e))

        return err_success
