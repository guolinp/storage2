#!/usr/bin/python

import json
from disk import FileDisk
from raid import RaidX
from lun import Lun


class BlockSystem(object):

    def __init__(self, system_db_name):
        self._system_db_name = system_db_name
        self.disks = {}
        self.raids = {}
        self.luns = {}
        self._build_device_tree()

    def _build_device_tree(self):
        # load device config from json
        with open(self._system_db_name) as f:
            sys_conf = json.load(f)

        # create disks
        disk_conf = sys_conf['disks']
        for conf in disk_conf:
            disk_name = conf['name']
            disk_pathname = conf['pathname']
            self.disks[disk_name] = FileDisk(disk_name, disk_pathname)

        # create raids
        raid_conf = sys_conf['raids']
        for conf in raid_conf:
            raid_name = conf['name']
            disk_list = conf['disks']
            raid = RaidX(raid_name)
            for disk_name in disk_list:
                raid.add_disk(self.disks[disk_name])
            self.raids[raid_name] = raid

        # create luns
        lun_conf = sys_conf['luns']
        for conf in lun_conf:
            lun_name = conf['name']
            raid_list = conf['raids']
            lun = Lun(lun_name)
            for raid_name in raid_list:
                lun.add_raid(self.raids[raid_name])
            self.luns[lun_name] = lun

    def dump_device_tree(self):
        for _, lun in self.luns.items():
            lun.dump_device_tree()


if __name__ == "__main__":
    bs = BlockSystem('system.json')
    bs.dump_device_tree()
    lun = bs.luns['LUN_0']

    test_string = 'x' * 1024 * 1024 * 4  # 4M
    test_string_length = len(test_string)
    offset = 1024 * 512

    lun.write(test_string, offset)

    result, read_string = lun.read(offset, test_string_length)

    if test_string == read_string:
        print('write == read')

    print('write length: %d' % test_string_length)
    print('read result: %d' % result)
    print('read length: %d' % len(read_string))
