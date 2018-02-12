#!/usr/bin/python

import struct

from error import *
from storage import Storage
from block_system import BlockSystem

BLOCK_SIZE = 4096
FS_MAGIC_NUMBER = 0xA0B1C2D3
INODE_MAGIC_NUMBER = 0x1A2B3C4D
INVALID_BLOCK_NUMBER = 0xFFFFFFFF
INODE_EMPTY_ENTRY = 0


class SuperBlock(object):

    def __init__(self):
        # default values
        self.magic = FS_MAGIC_NUMBER
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
        return self.magic == FS_MAGIC_NUMBER

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

    def __init__(self, block=INVALID_BLOCK_NUMBER):
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
        assert_true(self.block != INVALID_BLOCK_NUMBER)
        offset_in_device = self.block * BLOCK_SIZE
        result, data = device.read(offset_in_device, BLOCK_SIZE)
        if not is_success(result):
            raise DeviceAccessError(
                'read data from device failed, error  %d' % result)
        self.discard_cache()
        self._array = bytearray(data)

    def flush_to_device(self, device):
        assert_true(self.block != INVALID_BLOCK_NUMBER)
        offset_in_device = self.block * BLOCK_SIZE
        data = str(self._array)
        result = device.write(data, offset_in_device)
        if not is_success(result):
            raise DeviceAccessError(
                'flush data to device failed, error %d' % result)


class Inode(Storage):
    DIR_INODE = 0
    FILE_INODE = 1
    BAD_INODE = 2

    def __init__(self, fs, block, load=True):
        super(Inode, self).__init__()
        self._fs = fs
        self._magic = INODE_MAGIC_NUMBER
        self._inode_type = Inode.BAD_INODE
        self._parent = INVALID_BLOCK_NUMBER
        self._block = block
        self._cache = BlockCache()
        if load:
            self.load_inode()

    @property
    def inode_type(self):
        return self._inode_type

    @property
    def inode_type_str(self):
        if self._inode_type == Inode.DIR_INODE:
            return 'Dir Inode'
        elif self._inode_type == Inode.FILE_INODE:
            return 'File Inode'
        else:
            return 'Bad Inode'

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent

    @property
    def block(self):
        return self._block

    def _parse_inode(self):
        return True

    def _fill_inode(self):
        return True

    def _load_inode(self):
        assert_true(self.block != INVALID_BLOCK_NUMBER)
        self._cache.block = self._block
        self._cache.load_from_device(self._fs.device)

    def _flush_inode(self):
        assert_true(self.block != INVALID_BLOCK_NUMBER)
        self._cache.block = self._block
        self._cache.flush_to_device(self._fs.device)

    def load_inode(self):
        self._load_inode()
        self._parse_inode()

    def flush_inode(self):
        self._fill_inode()
        self._flush_inode()

    def dump_inode(self):
        print('\ninode (0x%0x)' % self.block)
        print('magic        : 0x%x' % self._magic)
        print('type         : %s' % self.inode_type_str)
        print('parent       : 0x%x' % self.parent)

# Dir Inode
#
#        0 :  Magic number
#        4 :  Byte[0]: inode type, byte[1..3]: reserved
#        8 :  Parent inode number
#       12 :  Next inode number
#    16~31 :  Reserved
#  32~4095 :  Inode number(dir/file)


class DirInode(Inode):

    def __init__(self, fs, block, load=True):
        # define memebers wihch may be used by super __init__
        self._inode_type = Inode.DIR_INODE
        self._entries = None
        self._next_inode = INVALID_BLOCK_NUMBER
        # call super class init
        super(DirInode, self).__init__(fs, block, load)

    @property
    def next_inode(self):
        return self._next_inode

    @next_inode.setter
    def next_inode(self, next_inode):
        self._next_inode = next_inode

    def _entry_offset_in_inode(self):
        return 32

    @property
    def max_entry_number(self):
        return (BLOCK_SIZE - 32) / 4

    def current_entry_count(self):
        result = 0
        if self._entries:
            for entry in self._entries:
                if entry != INODE_EMPTY_ENTRY:
                    result += 1
        return result

    def _is_valid_entry_index(self, index):
        if not self._entries:
            return False
        return index in range(0, len(self._entries))

    def alloc_entry(self):
        for index, entry in enumerate(self._entries):
            if entry == INODE_EMPTY_ENTRY:
                return index
        return -1

    def is_free(self, index):
        assert_true(self._is_valid_entry_index(index))
        return self._entries[index] == INODE_EMPTY_ENTRY

    def set_entry(self, index, inode_number):
        assert_true(self._is_valid_entry_index(index))
        self._entries[index] = inode_number

    def get_entry(self, index):
        assert_true(self._is_valid_entry_index(index))
        return self._entries[index]

    def free_entry(self, index):
        self.set_entry(index, INODE_EMPTY_ENTRY)

    def _parse_inode(self):
        # header
        header_size = 4 + 1 * 4 + 4 + 4
        header_fmt = 'IBBBBII'
        header = struct.unpack(header_fmt, self._cache.base[0:header_size])
        self._magic = header[0]
        self._inode_type = header[1]
        self._parent = header[5]
        self._next_inode = header[6]

        # entries
        entries_start = self._entry_offset_in_inode()
        entries_fmt = 'I' * self.max_entry_number
        entries = struct.unpack(entries_fmt, self._cache.base[entries_start:])
        self._entries = list(entries)

    def _fill_inode(self):
        self._magic = INODE_MAGIC_NUMBER
        # header
        header_fmt = 'IBBBBII'
        header_size = 4 + 1 * 4 + 4 + 4
        self._cache.base[0:header_size] = struct.pack(
            header_fmt, self._magic, self._inode_type, 0, 0, 0, self._parent, self._next_inode)

        # entries
        entries_fmt = 'I'
        entries_start = self._entry_offset_in_inode()
        if not self._entries:
            self._entries = [0 for i in range(0, self.max_entry_number)]
        for index, value in enumerate(self._entries):
            start = entries_start + 4 * index
            end = start + 4
            self._cache.base[start:end] = struct.pack(entries_fmt, value)

    def dump_inode(self, detail=False):
        super(DirInode, self).dump_inode()
        print('next_inode   : 0x%x' % self.next_inode)
        print('entry count  : %d' % self.current_entry_count())
        if detail:
            print('entries')
            for index in range(0, self.max_entry_number):
                print('    %4d : 0x%08x' % (index, self.get_entry(index)))

# File Inode
#
#        0 :  Magic number
#        4 :  byte[0]: inode type, byte[1..3]: reserved
#        8 :  Parent inode number
#       12 :  Size of file
#    16~31 :  Reserved
#    32~95 :  File name(max 64 bytes)
#   96~125 :  Data Block number(8 entries)
#      128 :  Indirect Block 1 number
#      132 :  Indirect Block 2 number
# 136~4095 : Reserved


class FileInode(Inode):

    def __init__(self, fs, block, load=True):
        # define memebers wihch may be used by super
        self._size = 0
        self._name = ''
        self._data_block_entries = []
        self._indirect_block1_entries = []
        self._indirect_block2_entries = []
        # call super class init
        super(FileInode, self).__init__(fs, block, load)
        # memebers which can not be changed by super class
        self._inode_type = Inode.FILE_INODE

    @property
    def size(self):
        return self._size

    # below defines reference the design
    @property
    def max_name_length(self):
        return 64

    def _file_name_offset_in_inode(self):
        return 32

    def _data_block_entry_offset_in_inode(self):
        return 96

    def _max_data_block_entry_number(self):
        return 8

    def _indirect_block1_entry_offset_in_inode(self):
        return 128

    def _max_indirect_block1_entry_number(self):
        return 1

    def _indirect_block2_entry_offset_in_inode(self):
        return 132

    def _max_indirect_block2_entry_number(self):
        return 1

    def _is_valid_data_block_entry_index(self, index):
        return 0 <= index < len(self._data_block_entries)

    def _is_valid_indirect_block1_entry_index(self, index):
        return 0 <= index < len(self._indirect_block1_entries)

    def _is_valid_indirect_block2_entry_index(self, index):
        return 0 <= index < len(self._indirect_block2_entries)

    # data block entries
    def set_data_block_entry(self, index, block):
        assert_true(self._is_valid_data_block_entry_index(index))
        self._data_block_entries[index] = block

    def get_data_block_entry(self, index):
        assert_true(self._is_valid_data_block_entry_index(index))
        return self._data_block_entries[index]

    def free_data_block_entry(self, index):
        self.set_data_block_entry(index, INODE_EMPTY_ENTRY)

    # indirect block1 entries
    def set_indirect_block1_entry(self, index, block):
        assert_true(self._is_valid_indirect_block1_entry_index(index))
        self._indirect_block1_entries[index] = block

    def get_indirect_block1_entry(self, index):
        assert_true(self._is_valid_indirect_block1_entry_index(index))
        return self._indirect_block1_entries[index]

    def free_indirect_block1_entry(self, index):
        self.set_indirect_block1_entry(index, INODE_EMPTY_ENTRY)

    # indirect block2 entries
    def set_indirect_block2_entry(self, index, block):
        assert_true(self._is_valid_indirect_block2_entry_index(index))
        self._indirect_block2_entries[index] = block

    def get_indirect_block2_entry(self, index):
        assert_true(self._is_valid_indirect_block2_entry_index(index))
        return self._indirect_block2_entries[index]

    def free_indirect_block2_entry(self, index):
        self.set_indirect_block2_entry(index, INODE_EMPTY_ENTRY)

    def _parse_inode(self):
        # header
        header_size = 4 + 1 * 4 + 4 + 4
        header_fmt = 'IBBBBII'
        header = struct.unpack(header_fmt, self._cache.base[0:header_size])
        self._magic = header[0]
        self._inode_type = header[1]
        self._parent = header[5]
        self._size = header[6]

        # name
        name_start = self._file_name_offset_in_inode()
        name_end = name_start + self.max_name_length
        name_fmt = 'B' * self.max_name_length
        self.name = struct.unpack(
            name_fmt, self._cache.base[name_start:name_end])

        # data block entries
        entries_start = self._data_block_entry_offset_in_inode()
        entries_end = entries_start + 4 * self._max_data_block_entry_number()
        entries_fmt = 'I' * self._max_data_block_entry_number()
        entries = struct.unpack(
            entries_fmt, self._cache.base[entries_start:entries_end])
        self._data_block_entries = list(entries)

        # indirect block1 entries
        entries_start = self._indirect_block1_entry_offset_in_inode()
        entries_end = entries_start + 4 * \
            self._max_indirect_block1_entry_number()
        entries_fmt = 'I' * self._max_indirect_block1_entry_number()
        entries = struct.unpack(
            entries_fmt, self._cache.base[entries_start:entries_end])
        self._indirect_block1_entries = list(entries)

        # indirect block2 entries
        entries_start = self._indirect_block2_entry_offset_in_inode()
        entries_end = entries_start + 4 * \
            self._max_indirect_block2_entry_number()
        entries_fmt = 'I' * self._max_indirect_block2_entry_number()
        entries = struct.unpack(
            entries_fmt, self._cache.base[entries_start:entries_end])
        self._indirect_block2_entries = list(entries)

    def _fill_inode(self):
        self._magic = INODE_MAGIC_NUMBER
        # header
        header_fmt = 'IBBBBII'
        header_size = 4 + 1 * 4 + 4 + 4
        self._cache.base[0:header_size] = struct.pack(
            header_fmt, self._magic, self._inode_type, 0, 0, 0, self._parent, self._size)

        # data block entries
        entries_fmt = 'I'
        entries_start = self._data_block_entry_offset_in_inode()
        if not self._data_block_entries:
            self._data_block_entries = [
                0 for i in range(0, self._max_data_block_entry_number())]
        for index, value in enumerate(self._data_block_entries):
            start = entries_start + 4 * index
            end = start + 4
            self._cache.base[start:end] = struct.pack(entries_fmt, value)

        # indirect block1 entries
        entries_fmt = 'I'
        entries_start = self._indirect_block1_entry_offset_in_inode()
        if not self._indirect_block1_entries:
            self._indirect_block1_entries = [
                0 for i in range(0, self._max_indirect_block1_entry_number())]
        for index, value in enumerate(self._indirect_block1_entries):
            start = entries_start + 4 * index
            end = start + 4
            self._cache.base[start:end] = struct.pack(entries_fmt, value)

        # indirect block1 entries
        entries_fmt = 'I'
        entries_start = self._indirect_block2_entry_offset_in_inode()
        if not self._indirect_block2_entries:
            self._indirect_block2_entries = [
                0 for i in range(0, self._max_indirect_block2_entry_number())]
        for index, value in enumerate(self._indirect_block2_entries):
            start = entries_start + 4 * index
            end = start + 4
            self._cache.base[start:end] = struct.pack(entries_fmt, value)

    def dump_inode(self):
        super(FileInode, self).dump_inode()
        print('size         : 0x%x' % self.size)
        print('data block entries')
        for index in range(0, self._max_data_block_entry_number()):
            print('    %4d : 0x%08x' %
                  (index, self.get_data_block_entry(index)))
        print('indirect block1 entries')
        for index in range(0, self._max_indirect_block1_entry_number()):
            print('    %4d : 0x%08x' %
                  (index, self.get_indirect_block1_entry(index)))
        print('indirect block2 entries')
        for index in range(0, self._max_indirect_block2_entry_number()):
            print('    %4d : 0x%08x' %
                  (index, self.get_indirect_block2_entry(index)))


class IndirectBlock(Storage):

    def __init__(self, fs, block, load=True):
        super(IndirectBlock, self).__init__()
        self._fs = fs
        self._block = block
        self._entries = []
        self._cache = BlockCache()
        if load:
            self.load_indirect_block()

    @property
    def block(self):
        return self._block

    @property
    def max_entry_number(self):
        return BLOCK_SIZE / 4

    @property
    def current_entry_count(self):
        result = 0
        if self._entries:
            for entry in self._entries:
                if entry != INODE_EMPTY_ENTRY:
                    result += 1
        return result

    def _is_valid_entry_index(self, index):
        return 0 <= index < len(self._entries)

    def load_indirect_block(self):
        assert_true(self.block != INVALID_BLOCK_NUMBER)
        self._cache.block = self._block
        self._cache.load_from_device(self._fs.device)

        entries_fmt = 'I' * self.max_entry_number
        entries = struct.unpack(entries_fmt, self._cache.base)
        self._entries = list(entries)

    def flush_indirect_block(self):
        assert_true(self.block != INVALID_BLOCK_NUMBER)

        entries_fmt = 'I'
        if not self._entries:
            self._entries = [0 for i in range(0, self.max_entry_number)]
        for index, value in enumerate(self._entries):
            start = 4 * index
            end = start + 4
            self._cache.base[start:end] = struct.pack(entries_fmt, value)

        self._cache.block = self._block
        self._cache.flush_to_device(self._fs.device)

    def alloc_entry(self):
        if self._entries:
            for index, entry in enumerate(self._entries):
                if entry == INODE_EMPTY_ENTRY:
                    return index
        return -1

    def is_free(self, index):
        assert_true(self._is_valid_entry_index(index))
        return self._entries[index] == INODE_EMPTY_ENTRY

    def set_entry(self, index, block):
        assert_true(self._is_valid_entry_index(index))
        self._entries[index] = block

    def get_entry(self, index):
        assert_true(self._is_valid_entry_index(index))
        return self._entries[index]

    def free_entry(self, index):
        self.set_entry(index, INODE_EMPTY_ENTRY)

    def dump_indirect_block(self, detail=False):
        print('\nindirect block (0x%x)' % self.block)
        print('entry count : %d' % self.current_entry_count)
        if detail:
            print('entries')
            for index in range(0, self.max_entry_number):
                if not self.is_free(index):
                    print('    %4d : 0x%08x' % (index, self.get_entry(index)))

# Indirect Block 1
#
#   0~4095 :  Data Block number


class IndirectBlock1(IndirectBlock):
    pass

# Indirect Block 2
#
#   0~4095 :  Indirect Block 1 number


class IndirectBlock2(IndirectBlock):
    pass


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


class FsFactory(object):

    @staticmethod
    def create_fs(name, device, size=0):
        return FileSystem(name, device, size, new=True)

    @staticmethod
    def attach_fs(name, device):
        return FileSystem(name, device, 0, new=False)


if __name__ == "__main__":

    bs = BlockSystem('system.json')
    lun = bs.luns['LUN_0']

    fs = FsFactory.create_fs('myfs', lun)
    # fs = FsFactory.attach_fs('myfs', lun)
    fs.sb.dump_super_block()

    inode = DirInode(fs, 73)
    inode.dump_inode()
#    inode.next_inode = 1200
#    index = inode.alloc_entry()
#    print 'free index %d' % index
#    inode.set_entry(index, 1300)
#    inode.flush_inode()
#    inode.dump_inode()

    finode = FileInode(fs, 768)
    finode.dump_inode()
#    for i in range(0,8):
#        finode.set_data_block_entry(i,i*128)
#    finode.set_indirect_block1_entry(0,110)
#    finode.set_indirect_block2_entry(0,120)
#    finode.flush_inode()
#    finode.dump_inode()
    ib = IndirectBlock1(fs, 1024)
    index = ib.alloc_entry()
    ib.set_entry(index, 32768)
    ib.dump_indirect_block(True)
    ib.flush_indirect_block()

    ib = IndirectBlock2(fs, 1025)
    index = ib.alloc_entry()
    ib.set_entry(index, 32768)
    ib.dump_indirect_block(True)
    ib.flush_indirect_block()
