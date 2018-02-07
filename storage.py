#!/usr/bin/python

from log import Logger


class Storage(object):

    def __init__(self, log_filename='runtime.log'):
        self.logger = Logger.get_logger(log_filename)
