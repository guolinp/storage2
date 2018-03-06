#!/usr/bin/python

from error import *
from storage import Storage
from device import Device

RAID_DEFAULT_STRIPE = 1 * 1024 * 1024  # 1M


class Extent(Storage):

    def __init__(self, device, start, length):
        self.device = device
        self.start = start
        self.length = length


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

    def _make_extents(self, offset, length):
        raise NeedToBeImplementedError('need to implement by sub-class')

    def read(self, offset, length):
        self.logger.debug('start read on %s, offset %d, length %d' %
                          (self.name, offset, length))
        if not self.is_valid_range(offset, length):
            return err_invalid_argument, None
        data = []
        extents = self._make_extents(offset, length)
        for extent in extents:
            result, read_data = extent.device.read(extent.start, extent.length)
            if not is_success(result):
                break
            data.append(read_data)
        return result, ''.join(data)

    def write(self, data, offset):
        self.logger.debug('start write on %s: offset %d, length %d' %
                          (self.name, offset, 0 if data is None else len(data)))
        if data is None:
            return err_invalid_argument
        length = len(data)
        if not self.is_valid_range(offset, length):
            return err_invalid_argument
        write_offset = 0
        extents = self._make_extents(offset, length)
        for extent in extents:
            data_to_be_wrote = data[write_offset:write_offset + extent.length]
            result = extent.device.write(data_to_be_wrote, extent.start)
            if not is_success(result):
                break
            write_offset += extent.length
        return result


class Raid0(Raid):

    @property
    def info(self):
        return 'Raid0'

    def build(self):
        if len(self._children) > 0:
            return err_success
        self.logger.error('no disk in raid')
        return err_disk_not_enough

    # this is not a real raid0, we perform data IO on disks one by one.
    # to be improved
    def _make_extents(self, offset, length):
        offset_passed = 0
        extents = []

        for device in self._children:
            # find the first device in the io range
            if offset > offset_passed + device.size:
                offset_passed += device.size
                continue
            if offset > offset_passed:
                offset_in_curr_dev = offset - offset_passed
            else:
                offset_in_curr_dev = 0
            if length <= device.size - offset_in_curr_dev:
                length_in_curr_dev = length
            else:
                length_in_curr_dev = device.size - offset_in_curr_dev
            extents.append(
                Extent(device, offset_in_curr_dev, length_in_curr_dev))
            # increase the offset for next device mapping
            offset_passed += device.size
            length -= length_in_curr_dev
            if length == 0:
                break
        return extents


class Raid1(Raid):

    def __init__(self, name, stripe=RAID_DEFAULT_STRIPE):
        raise FunctionalNotImplementError('Raid1')


class Raid01(Raid):

    def __init__(self, name, stripe=RAID_DEFAULT_STRIPE):
        raise FunctionalNotImplementError('Raid01')


class Raid10(Raid):

    def __init__(self, name, stripe=RAID_DEFAULT_STRIPE):
        raise FunctionalNotImplementError('Raid10')


class Raid5(Raid):

    def __init__(self, name, stripe=RAID_DEFAULT_STRIPE):
        raise FunctionalNotImplementError('Raid5')
