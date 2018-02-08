#!/usr/bin/python

import struct

from error import *
from storage import Storage
from block_system import BlockSystem

BLOCK_SIZE = 4096
FS_MAGIC_NUM = 0xA0B1C2D3


class SuperBlock(object):

    def __init__(self):
        # default values
        self.magic = FS_MAGIC_NUM
        self.sb_start_block = 0
        self.sb_blocks = 1
        self.inode_bitmap_start_block = self.sb_start_block + self.sb_blocks
        self.inode_bitmap_blocks = 8
        self.data_bitmap_start_block = self.inode_bitmap_start_block + \
            self.inode_bitmap_blocks
        self.data_bitmap_blocks = 64
        self.inode_start_block = self.data_bitmap_start_block + \
            self.data_bitmap_blocks
        self.inode_blocks = 8 * BLOCK_SIZE
        self.data_start_block = self.inode_start_block + self.inode_blocks
        self.data_blocks = 64 * BLOCK_SIZE

    def metadata_space_size(self):
        blocks = self.sb_blocks
        blocks += self.inode_bitmap_blocks
        blocks += self.data_bitmap_blocks
        blocks += self.inode_blocks
        return blocks * BLOCK_SIZE

    def adjust_data_space_size(self, size):
        self.data_blocks = size / BLOCK_SIZE

    def is_valid(self):
        # a simple check
        return self.magic == FS_MAGIC_NUM

    def load_from_block_cache(self, bc):
        sb_fmt = 'I' * 11
        sb_size_on_disk = 44
        self.magic, self.sb_start_block, self.sb_blocks, self.inode_bitmap_start_block, self.inode_bitmap_blocks, self.data_bitmap_start_block, self.data_bitmap_blocks, self.inode_start_block, self.inode_blocks, self.data_start_block, self.data_blocks = struct.unpack(
            sb_fmt, bc.base[0:sb_size_on_disk])

    def flush_to_block_cache(self, bc):
        sb_fmt = 'I' * 11
        sb_size_on_disk = 44
        buf = struct.pack(
            sb_fmt, self.magic, self.sb_start_block, self.sb_blocks, self.inode_bitmap_start_block, self.inode_bitmap_blocks, self.data_bitmap_start_block, self.data_bitmap_blocks, self.inode_start_block, self.inode_blocks, self.data_start_block, self.data_blocks)
        bc.base[0:sb_size_on_disk] = buf

    def dump_super_block(self):
        print('magic                    : 0x%x' % self.magic)
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

    def __init__(self, block=0xffffffff):
        self.block = block
        self._array = bytearray(BLOCK_SIZE)

    @property
    def base(self):
        return self._array

    @property
    def size(self):
        return BLOCK_SIZE

    def discard_cache(self):
        if self._array is not None:
            del self._array

    def zero_cache(self):
        self.discard_cache()
        self._array = bytearray(BLOCK_SIZE)

    def load_from_device(self, device):
        offset_in_device = self.block * BLOCK_SIZE
        result, data = device.read(offset_in_device, BLOCK_SIZE)
        if not is_success(result):
            raise DeviceAccessError(
                'read data from device failed, error  %d' % result)
        self.discard_cache()
        self._array = bytearray(data)

    def flush_to_device(self, device):
        offset_in_device = self.block * BLOCK_SIZE
        data = str(self._array)
        result = device.write(data, offset_in_device)
        if not is_success(result):
            raise DeviceAccessError(
                'flush data to device failed, error %d' % result)


class FileSystem(Storage):

    def __init__(self, name, device, size=0, new=False):
        super(FileSystem, self).__init__()
        self.name = name
        self.device = device
        self.size = size
        self.sb = SuperBlock()
        self._init_super_block()
        if new:
            self.flush_super_block()
            self.clear_bitmap_space()
        else:
            self.load_super_block()
            if not self.sb.is_valid():
                raise BadSuperBlockError('bad super block data')

    def _init_super_block(self):
        if self.size == 0:
            self.size = self.device.size
        elif self.size > self.device.size:
            self.size = self.device.size
        elif self.size < self.sb.metadata_space_size():
            raise DeviceNoEnoughSpaceError(
                'device %s have no enough space' % self.device.name)
        else:
            pass
        data_space_size = self.size - self.sb.metadata_space_size()
        self.sb.adjust_data_space_size(data_space_size)

    def load_super_block(self):
        bc = BlockCache(0)
        bc.load_from_device(self.device)
        self.sb.load_from_block_cache(bc)
        bc.discard_cache()

    def flush_super_block(self):
        bc = BlockCache(0)
        self.sb.flush_to_block_cache(bc)
        bc.flush_to_device(self.device)
        bc.discard_cache()

    def _find_free_block(self, start_block, end_block):
        '''
        this function search the bitmap to find a free block in the given subspace,
        returns a block offset in the subspace, so to get the global block offset,
        need to add the space base. if there is not any free block, return -1
        '''
        free_block_offset = -1
        # Note: we are using a byte to mark if a block is free, not a bitmap now.
        # so the unit we are searching is byte
        # entry_per_block = BLOCK_SIZE / 1
        bc = BlockCache()
        for offset, block in enumerate(range(start_block, end_block)):
            bc.block = block
            bc.load_from_device(self.device)
            for index in range(0, bc.size):
                if bc.base[index] == 0:
                    free_block_offset = offset * bc.size + index
                    bc.discard_cache()
                    return free_block_offset
        bc.discard_cache()
        return free_block_offset

    def find_free_inode_block(self):
        '''find a free inode block, return the block offset in fs space'''
        start_block = self.sb.inode_bitmap_start_block
        end_block = start_block + self.sb.inode_bitmap_blocks
        free_block_offset = self._find_free_block(start_block, end_block)
        if free_block_offset != -1:
            if free_block_offset < self.sb.inode_blocks:
                free_block_offset += self.sb.inode_start_block
            else:
                # the inode block is not enough on device even thougth
                # we have bitmap place, return no free inode block
                free_block_offset = -1
        return free_block_offset

    def find_free_data_block(self):
        '''find a free data block, return the block offset in fs space'''
        start_block = self.sb.data_bitmap_start_block
        end_block = start_block + self.sb.data_bitmap_blocks
        free_block_offset = self._find_free_block(start_block, end_block)
        if free_block_offset != -1:
            if free_block_offset < self.sb.data_blocks:
                free_block_offset += self.sb.data_start_block
            else:
                # the data block is not enough on device even thougth
                # we have bitmap place, return no free data block
                free_block_offset = -1
        return free_block_offset

    def update_bitmap(self, block, value):
        # blocks are not managed by bitmap
        if block < self.sb.inode_start_block:
            return
        # go to here means that the block is a data or inode block
        if block < self.sb.data_start_block:
            # inode block
            block_offset = block - self.sb.inode_start_block
            bitmap_start_block = self.sb.inode_bitmap_start_block
        else:
            # data block
            block_offset = block - self.sb.data_start_block
            bitmap_start_block = self.sb.data_bitmap_start_block
        # get the block offset in bitmap space
        offset = block_offset / BLOCK_SIZE
        # get the entry index in a block
        index = block_offset % BLOCK_SIZE
        # read-modify-write
        bc = BlockCache(bitmap_start_block + offset)
        bc.load_from_device(self.device)
        bc.base[index] = value
        bc.flush_to_device(self.device)
        bc.discard_cache()

    def mark_block_used(self, block):
        self.update_bitmap(block, 1)

    def mark_block_free(self, block):
        self.update_bitmap(block, 0)

    def clear_bitmap_space(self):
        # inode bitmap
        start_block = self.sb.inode_bitmap_start_block
        end_block = start_block + self.sb.inode_bitmap_blocks
        # make a blocks list for inode blocks
        blocks = range(start_block, end_block)
        # data bitmap
        start_block = self.sb.data_bitmap_start_block
        end_block = start_block + self.sb.data_bitmap_blocks
        # add data blocks
        blocks.extend(range(start_block, end_block))
        # zero these blocks
        bc = BlockCache()
        bc.zero_cache()
        for block in blocks:
            bc.block = block
            bc.flush_to_device(self.device)
        bc.discard_cache()

    def mount(self):
        return err_success

    def unmount(self):
        return err_success

    def ls(self, pathname):
        raise FunctionalNotImplementError('ls')

    def mkdir(self, pathname):
        raise FunctionalNotImplementError('mkdir')

    def rmdir(self, pathname):
        raise FunctionalNotImplementError('rmdir')

    def create_file(self, pathname):
        raise FunctionalNotImplementError('create_file')

    def remove_file(self, pathname):
        raise FunctionalNotImplementError('remove_file')

    def read_file(self, pathname, offset, length):
        raise FunctionalNotImplementError('read_file')

    def write_file(self, pathname, data, offset):
        raise FunctionalNotImplementError('write_file')


class FsTool(object):

    @staticmethod
    def create_fs(name, device, size=0):
        return FileSystem(name, device, size, new=True)

    @staticmethod
    def attach_fs(name, device):
        return FileSystem(name, device, 0, new=False)


if __name__ == "__main__":
    bs = BlockSystem('system.json')
    lun = bs.luns['LUN_0']

    fs = FsTool.create_fs('myfs', lun)
    # fs = FsTool.attach_fs('myfs', lun)
    fs.sb.dump_super_block()
