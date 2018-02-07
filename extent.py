#!/usr/bin/python

from storage import Storage

class Extent(Storage):

    def __init__(self, device, start, length):
        self.device = device
        self.start = start
        self.length = length

    def __str__(self):
        return 'Extent: device %s, start %d, length %d' % (self.device.name, self.start, self.length)
