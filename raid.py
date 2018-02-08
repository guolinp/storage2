#!/usr/bin/python

from device import Device


class Raid(Device):

    def add_disk(self, disk):
        self.add_child(disk)

    def remove_disk(self, disk):
        self.remove_child(disk)


class RaidX(Raid):

    '''Not a real RAID, just combine some disks to a virtual disk'''

    @property
    def info(self):
        return 'RaidX, a fake raid'
