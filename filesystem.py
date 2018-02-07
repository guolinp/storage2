#!/usr/bin/python

from error import *
import block
import struct

BLOCK_SIZE = 4096


class SuperBlock(object):

    def __init__(self):
        # default values
        self.sb_start_block = 0
        self.sb_blocks = 1
        self.inode_bitmap_start_block = self.sb_start_block + self.sb_blocks
        self.inode_bitmap_blocks = 8
        self.data_bitmap_start_block = self.inode_bitmap_start_block + \
            self.inode_bitmap_blocks
        self.data_bitmap_blocks = 64
        self.inode_start_block = self.data_bitmap_start_block + \
            self.data_bitmap_blocks
        self.inode_blocks = 8 * 1024
        self.data_start_block = self.inode_start_block + self.inode_blocks
        self.data_blocks = 256 * 1024

    def metadata_space_size(self):
        blocks = self.sb_blocks
        blocks += self.inode_bitmap_blocks
        blocks += self.data_bitmap_blocks
        blocks += self.inode_blocks
        return blocks * BLOCK_SIZE

    def adjust_data_space_size(self, size):
        self.data_blocks = size / BLOCK_SIZE

    def load_from_block_cache(self, bc):
        sb_fmt = 'I' * 10
        sb_size_on_disk = 40
        self.sb_start_block, self.sb_blocks, self.inode_bitmap_start_block, self.inode_bitmap_blocks, self.data_bitmap_start_block, self.data_bitmap_blocks, self.inode_start_block, self.inode_blocks, self.data_start_block, self.data_blocks = struct.unpack(sb_fmt, bc.base[0:sb_size_on_disk])

    def flush_to_block_cache(self, bc):
        sb_fmt = 'I' * 10
        sb_size_on_disk = 40
        buf = struct.pack(
            sb_fmt, self.sb_start_block, self.sb_blocks, self.inode_bitmap_start_block, self.inode_bitmap_blocks, self.data_bitmap_start_block, self.data_bitmap_blocks, self.inode_start_block, self.inode_blocks, self.data_start_block, self.data_blocks)
        bc.base[0:sb_size_on_disk] = buf

    def dump_super_block(self):
        print('sb_start_block           : %d' % self.sb_start_block)
        print('sb_blocks                : %d' % self.sb_blocks)
        print('inode_bitmap_start_block : %d' % self.inode_bitmap_start_block)
        print('inode_bitmap_blocks      : %d' % self.inode_bitmap_blocks)
        print('data_bitmap_start_block  : %d' % self.data_bitmap_start_block)
        print('data_bitmap_blocks       : %d' % self.data_bitmap_blocks)
        print('inode_start_block        : %d' % self.inode_start_block)
        print('inode_blocks             : %d' % self.inode_blocks)
        print('data_start_block         : %d' % self.data_start_block)
        print('data_blocks              : %d' % self.data_blocks)


class BlockCache(object):

    def __init__(self, device, lbn):
        self._device = device
        self._lbn = lbn
        self._buffer = bytearray(BLOCK_SIZE)

    @property
    def base(self):
        return self._buffer

    @property
    def lbn(self):
        return self._lbn

    def load_from_device(self):
        offset_in_device = self._lbn * BLOCK_SIZE
        result, data = self._device.read(offset_in_device, BLOCK_SIZE)
        if not is_success(result):
            raise DeviceAccessError(
                'read data from device failed, error  %d' % result)
        self.discard()
        self._buffer = bytearray(data)

    def flush_to_device(self):
        offset_in_device = self._lbn * BLOCK_SIZE
        data = str(self._buffer)
        result = self._device.write(data, offset_in_device)
        if not is_success(result):
            raise DeviceAccessError(
                'flush data to device failed, error %d' % result)

    def discard(self):
        if self._buffer is not None:
            del self._buffer
            self._buffer = None


class FileSystem(object):

    def __init__(self, name, device, size):
        self.name = name
        self.device = device
        self.size = size
        self.sb = SuperBlock()
        self._init_super_block()

    def _init_super_block(self):
        if self.size > self.device.size:
            self.size = self.device.size
        if self.size < self.sb.metadata_space_size():
            raise DeviceNoEnoughSpaceError(
                'device %s have no enough space' % self.device.name)
        data_space_size = self.size - self.sb.metadata_space_size()
        self.sb.adjust_data_space_size(data_space_size)

    def load_super_block(self):
        bc = BlockCache(self.device, 0)
        bc.load_from_device()
        self.sb.load_from_block_cache(bc)
        bc.discard()

    def flush_super_block(self):
        bc = BlockCache(self.device, 0)
        self.sb.flush_to_block_cache(bc)
        bc.flush_to_device()
        bc.discard()

    def _find_free_block(self, start_lbn, end_lbn):
        '''
        this function search the bitmap to find a free block in the given space range,
        returns a block offset in the space, so to get the global lbn, need to add the space base.
        if there is not any free block, return -1
        '''
        free_block = -1
        # Note: we are using a byte to mark if a block is free, not a bitmap now.
        # so the unit we are searching is byte
        entry_per_block = BLOCK_SIZE / 1
        for offset, lbn in enumerate(range(start_lbn, end_lbn)):
            bc = BlockCache(self.device, lbn)
            for i in range(0, len(bc.base)):
                if bc.base[i] == 0:
                    free_block = offset * entry_per_block + i
                    return free_block
        return free_block

    def find_free_inode_block(self):
        start_block = self.sb.inode_bitmap_start_block
        end_block = start_block + self.sb.inode_bitmap_blocks
        free_block = self._find_free_block(start_block, end_block)
        if free_block != -1:
            free_block += self.sb.inode_start_block
        return free_block

    def find_free_data_block(self):
        start_block = self.sb.data_bitmap_start_block
        end_block = start_block + self.sb.data_bitmap_blocks
        free_block = self._find_free_block(start_block, end_block)
        if free_block != -1:
            free_block += self.sb.data_start_block
        return free_block


lun = block.get_default_lun()

fs = FileSystem('myFs', lun, 1024 * 1024 * 512)
fs.sb.dump_super_block()
fs.flush_super_block()
print fs.find_free_inode_block()
print fs.find_free_data_block()
fs.load_super_block()
fs.sb.dump_super_block()
