#!/usr/bin/python

from storage import Storage


class Extent(Storage):

    def __init__(self, device, start, length):
        self.device = device
        self.start = start
        self.length = length
