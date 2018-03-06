#!/usr/bin/python

from device import Device
from raid import Raid0


class Lun(Device):

    def __init__(self, name):
        super(Lun, self).__init__(name)
        # LUN manages raids by a Raid0 model
        self._raid0 = Raid0('InternalRaid0')
        self.add_child(self._raid0)

    def add_raid(self, raid):
        self._raid0.add_child(raid)

    def remove_raid(self, raid):
        self._raid0.remove_child(raid)

    def read(self, offset, length):
        return self._raid0.read(offset, length)

    def write(self, data, offset):
        return self._raid0.write(data, offset)
