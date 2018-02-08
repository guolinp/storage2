#!/usr/bin/python

from error import *
from device import Device

RAID_DEFAULT_STRIPE = 1 * 1024 * 1024  # 1M


class Raid(Device):

    def __init__(self, name, stripe=RAID_DEFAULT_STRIPE):
        super(Raid, self).__init__(name)
        self._stripe = stripe

    @property
    def stripe(self):
        return self._stripe

    def add_disk(self, disk):
        self.add_child(disk)

    def remove_disk(self, disk):
        self.remove_child(disk)

    def build(self):
        return err_success


class RaidX(Raid):

    '''Not a real RAID, just combine some disks to a virtual disk'''

    @property
    def info(self):
        return 'RaidX, a fake raid'

    def build(self):
        if len(self._children) > 0:
            return err_success
        self.logger.error('no disk in raid')
        return err_disk_not_enough


class Raid0(Raid):

    def __init__(self):
        raise FunctionalNotImplementError('Raid0')


class Raid1(Raid):

    def __init__(self):
        raise FunctionalNotImplementError('Raid1')


class Raid01(Raid):

    def __init__(self):
        raise FunctionalNotImplementError('Raid01')


class Raid10(Raid):

    def __init__(self):
        raise FunctionalNotImplementError('Raid10')


class Raid5(Raid):

    def __init__(self):
        raise FunctionalNotImplementError('Raid5')
