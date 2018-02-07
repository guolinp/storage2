#!/usr/bin/python

from disk import FileDisk
from raid import RaidX
from lun import Lun


disks = []
for i in range(10):
    disk_name = 'DISK_%d' % i
    disks.append(FileDisk(disk_name))

raids = []
for i in range(2):
    raid_name = 'RAID_%d' % i
    raids.append(RaidX(raid_name))

lun = Lun('LUN_0')

for i in range(5):
    raids[0].add_disk(disks[i])
for i in range(5, 10):
    raids[1].add_disk(disks[i])
for i in range(2):
    lun.add_raid(raids[i])

lun.dump_device_tree()

test_string = 'x' * 1024 * 1024 * 4 #4M
lun.write(test_string, 1024*512)
result, read_string = lun.read(1024*512, len(test_string))
print 'write length: %d' % len(test_string)
print 'result: %d' % result
print 'read length: %d' % len(read_string)

