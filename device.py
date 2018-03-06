#!/usr/bin/python

from error import *
from storage import Storage


class Device(Storage):

    '''device base class'''

    def __init__(self, name):
        super(Device, self).__init__()
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
    def info(self):
        return ''

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent

    @property
    def num_child(self):
        return len(self._children)

    def update_size(self):
        self._size = 0
        # update me
        for dev in self._children:
            self._size += dev.size
        # invoke parent to update
        if self.parent is not None:
            self.parent.update_size()

    def add_child(self, child):
        if child not in self._children:
            self._children.append(child)
            child.parent = self
            self.update_size()

    def remove_child(self, child):
        if child in self._children:
            self._children.remove(child)
            self.update_size()

    def is_valid_range(self, offset, length):
        return offset >= 0 and length > 0 and offset + length < self.size

    def read(self, offset, length):
        raise NeedToBeImplementedError('need to implement by sub-class')

    def write(self, data, offset):
        raise NeedToBeImplementedError('need to implement by sub-class')

    def dump_device_tree(self, level=0):
        print('%s-->%s (size: %d %s)' %
              ('  ' * level, self.name, self.size, self.info))
        level += 1
        for device in self._children:
            device.dump_device_tree(level)
