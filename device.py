#!/usr/bin/python

from error import *
from storage import Storage
from extent import Extent


class Device(Storage):
    '''device framework'''
    def __init__(self, name):
        Storage.__init__(self)
        self._name = name
        self._size = 0
        self._parent = None
        self._children = []

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        return self._size

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent

    def _update_size(self):
        self._size = 0
        for dev in self._children:
            self._size += dev.size

    def add_child(self, child):
        if child not in self._children:
            self._children.append(child)
            child.parent = self
            self._update_size()

    def remove_child(self, child):
        if child in self._children:
            self._children.remove(child)
            self._update_size()

    def _is_valid_range(self, offset, length):
        if offset < 0 or length <= 0:
            return False
        if offset + length > self.size:
            return False
        return True

    # the function performs io request address mapping
    def _make_extents(self, offset, length):
        offset_passed = 0
        extents = []

        for device in self._children:
            # find the first device in the io range
            if offset > offset_passed + device.size:
                offset_passed += device.size
                continue

            if offset > offset_passed:
                offset_in_curr_dev = offset - offset_passed
            else:
                offset_in_curr_dev = 0

            if length <= device.size - offset_in_curr_dev:
                length_in_curr_dev = length
            else:
                length_in_curr_dev = device.size - offset_in_curr_dev

            extents.append(
                Extent(device, offset_in_curr_dev, length_in_curr_dev))

            # increase the offset for next device mapping
            offset_passed += device.size
            length -= length_in_curr_dev

            if length == 0:
                break

        return extents

    # the read/write is a default behavior, sub-class may override them.
    # it considers that all the children combine a virtual device,
    # they are sharing a liner device space.
    def read(self, offset, length):
        self.logger.debug('start read on %s, offset %d, length %d' % (self._name, offset, length))
        if not self._is_valid_range(offset, length):
            return err_invalid_argument, None

        data = []
        extents = self._make_extents(offset, length)
        for extent in extents:
            result, read_data = extent.device.read(extent.start, extent.length)
            if not is_success(result):
                break
            data.append(read_data)
        return result, ''.join(data)

    def write(self, data, offset):
        self.logger.debug('start write on %s: offset %d, length %d' % (self._name, offset, 0 if data is None else len(data)))

        if data is None:
            return err_invalid_argument

        length = len(data)

        if not self._is_valid_range(offset, length):
            return err_invalid_argument

        write_offset = 0
        extents = self._make_extents(offset, length)
        for extent in extents:
            data_to_be_wrote = data[write_offset:write_offset + extent.length]
            result = extent.device.write(data_to_be_wrote, extent.start)
            if not is_success(result):
                break
            write_offset += extent.length
        return result

    def dump_device_tree(self, level=0):
        print '%s-->%s (size: %d)' % ('  ' * level, self._name, self._size)
        level += 1
        for device in self._children:
            device.dump_device_tree(level)
