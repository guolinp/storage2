#!/usr/bin/python

from device import Device


class Lun(Device):

    def add_raid(self, raid):
        self.add_child(raid)

    def remove_raid(self, raid):
        self.remove_child(raid)
