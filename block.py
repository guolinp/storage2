#!/usr/bin/python

from disk import FileDisk
from raid import RaidX
from lun import Lun

import json


def build_device_tree(filename):
    # load device config from json
    with open(filename) as f:
        sys_conf = json.load(f)

    # create disks
    disks = {}
    disk_conf = sys_conf['disks']
    for conf in disk_conf:
        disk_name = conf['name']
        disk_pathname = conf['pathname']
        disks[disk_name] = FileDisk(disk_name, disk_pathname)

    # create raids
    raids = {}
    raid_conf = sys_conf['raids']
    for conf in raid_conf:
        raid_name = conf['name']
        disk_list = conf['disks']
        raid = RaidX(raid_name)
        for disk_name in disk_list:
            raid.add_disk(disks[disk_name])
        raids[raid_name] = raid

    # create luns
    luns = {}
    lun_conf = sys_conf['luns']
    for conf in lun_conf:
        lun_name = conf['name']
        raid_list = conf['raids']
        lun = Lun(lun_name)
        for raid_name in raid_list:
            lun.add_raid(raids[raid_name])
        luns[lun_name] = lun

    return luns


def dump_device_tree(luns):
    for _, lun in luns.items():
        lun.dump_device_tree()

def get_default_lun():
    luns = build_device_tree('system.json')
    return luns['LUN0']

if __name__ == "__main__":
    luns = build_device_tree('system.json')
    dump_device_tree(luns)

    lun = luns['LUN0']

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
