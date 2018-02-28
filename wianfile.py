# Copyright (c) Andrew Li 2018. This file is licensed under the GPLv3.
# See https://github.com/andrew0x4c/wian for more information,
# including the full LICENSE file.

import os
import base_utils
import file_utils

class WIANFile:
    """
    Represents a "file" (actually a directory) stored in the WIAN format
    """
    def __init__(self, dirname, create=False):
        """
        Constructs a WIANFile object

        With `create=True`, creates a new WIAN file with the given name.
        With `create=False`, wraps an an already-created WIAN file.
        """
        self.dirname = dirname
        if create:
            os.mkdir(dirname)
            os.mkdir(os.path.join(dirname, "data"))
            os.mkdir(os.path.join(dirname, "size"))
            file_utils.touch(os.path.join(dirname, "size", "+"))
            self.size = 0
            self._depth = 0
        else:
            self.size = self._read_entry("size")
            self._depth = max(base_utils.num_hex_needed(self.size) - 2, 0)
        # you shouldn't directly read the depth, so it's private

    # reading/writing metadata entries

    def _read_entry(self, entry):
        path = os.path.join(self.dirname, entry)
        item_strs = os.listdir(path)
        item_strs = [x for x in item_strs if x[0] == "+"]
        if len(item_strs) == 0:
            raise ValueError("No {} entry".format(entry))
        if len(item_strs) >= 2:
            raise ValueError("Multiple {} entries".format(entry))
        item_str = item_strs[0]
        b64_digits = base_utils.base64_to_list(item_str[1:])
        return base_utils.from_base(b64_digits, 64)

    def _write_entry(self, entry, num):
        path = os.path.join(self.dirname, entry)
        item_strs = os.listdir(path)
        file_utils.remove_all(path)
        b64_digits = base_utils.to_base(num, 64)
        item_str = "+" + base_utils.list_to_base64(b64_digits)
        file_utils.touch(os.path.join(path, item_str))

    # get a list of paths from the root of the tree to a specific block

    def _paths_from_block_num(self, block_num):
        assert block_num < 1 << (4 * self._depth)
        if self._depth > 0:
            hex_str = ("{:0>" + str(self._depth) + "x}").format(block_num)
        else:
            hex_str = ""
        # always returns the data subdirectory - remember to slice it off
        # if you don't need it!
        return [os.path.join(self.dirname, "data", *hex_str[:i])
            for i in range(len(hex_str) + 1)]

    # add/remove layers, when the file grows/shrinks

    def _add_layer(self):
        # even though it would be easier, we don't make a data_ temporarily
        # because it would change the modification time of the top-level dir
        item_strs = os.listdir(os.path.join(self.dirname, "data"))
        if item_strs:
            os.mkdir(os.path.join(self.dirname, "data", "new_0"))
            for item_str in item_strs:
                os.rename(
                    os.path.join(self.dirname, "data", item_str),
                    os.path.join(self.dirname, "data", "new_0", item_str))
            os.rename(
                os.path.join(self.dirname, "data", "new_0"),
                os.path.join(self.dirname, "data", "0"))
            # if there are none, that means the file is empty and we should
            # not try to make 0/0/0/0, for instance
        self._depth += 1

    def _remove_layer(self):
        # make sure the only thing left is 0 before removing!
        item_strs = os.listdir(os.path.join(self.dirname, "data", "0"))
        os.rename(
            os.path.join(self.dirname, "data", "0"),
            os.path.join(self.dirname, "data", "old_0"))
        for item_str in item_strs:
            os.rename(
                os.path.join(self.dirname, "data", "old_0", item_str),
                os.path.join(self.dirname, "data", item_str))
        os.rmdir(os.path.join(self.dirname, "data", "old_0"))
        self._depth -= 1
    
    # automatically manage adding/removing layers and blocks
    # based on the new size

    def _expand_to(self, new_size):
        while 1 << (4 * (self._depth + 2)) < new_size:
            # while the depth is not enough
            self._add_layer()
        self.size = new_size
        self._write_entry("size", new_size)

    def _truncate_to(self, new_size):
        # this function was hard to implement cleanly
        last_block = max((new_size + 255) / 256 - 1, 0) # last block to keep
        target_hexes = base_utils.to_base_pad(last_block, 16, self._depth)
        curr_path = os.path.join(self.dirname, "data")
        curr_hexes = []
        for d in range(self._depth):
            item_strs = os.listdir(curr_path)
            item_strs.sort(key=lambda c: int(c, 16), reverse=True)
            done = False
            for item_str in item_strs:
                potential_path = os.path.join(curr_path, item_str)
                potential_hexes = curr_hexes + [int(item_str, 16)]
                if potential_hexes > target_hexes:
                    # this never will contain our block
                    file_utils.remove_recursive(potential_path)
                elif potential_hexes == target_hexes[:len(potential_hexes)]:
                    curr_path = potential_path
                    curr_hexes = potential_hexes
                    break
                else: # "oops, missed it" - we can stop
                    # always will contain our block from here on
                    done = True
                    break
            if done: break
        # now, we may have some unneeded 0/0/0/..., so we need to
        # call _remove_layer
        data_path = os.path.join(self.dirname, "data")
        while True:
            # I used while True here to avoid putting "heavy" function calls
            # (in this case, listdir - it performs syscalls!) in a condition
            item_strs = os.listdir(data_path)
            if len(item_strs) != 1: break
            self._remove_layer()
        # finally, clear the potential partial extra block at the end
        partial = new_size % 256
        if partial:
            block_num = new_size / 256
            block = self.read_block(block_num)
            block = block[:partial] + (256 - partial) * [0]
            self.write_block(block_num, block)
            # if the result is all 0, write_block automatically clears it
        self.size = new_size
        self._write_entry("size", new_size)

    def resize(self, new_size):
        """
        Resizes the WIAN file
        """
        if new_size > self.size:
            self._expand_to(new_size)
        elif new_size < self.size:
            self._truncate_to(new_size)
        else: # new_size == self.size
            pass

    # block-level read/writes

    def read_block(self, block_num):
        """
        Reads the block with index `block_num`

        Returns a list of integers representing the bytes in the block.

        It is recommended to read data with `read_all` instead, to avoid
        having to manage offsets within blocks and reading partial blocks.
        """
        paths = self._paths_from_block_num(block_num)
        for path in paths[1:]: # don't check data subdir
            if not os.path.isdir(path):
                return [0] * 256
        path = paths[-1] # may be data subdir, if only 1 block
        item_strs = os.listdir(path)
        items = [[0] * 16 for _ in range(16)]
        used_idx = set()
        for item_str in item_strs:
            if item_str[0] != "+": continue
            idx, item = base_utils.decode(
                base_utils.base64_to_list(item_str[1:]))
            if idx in used_idx:
                raise ValueError(
                    "Corrupted block: {} (multiple items for index {})"
                    .format(block_num, idx)
                )
            used_idx.add(idx)
            items[idx] = item
        data = [num for item in items for num in item]
        return data

    def write_block(self, block_num, data):
        """
        Writes to the block with index `block_num`

        Takes a list of integers `data` representing the bytes in the block.

        It is recommended to write data with `write_all` instead, to avoid
        having to manage offsets within blocks and writing partial blocks.
        """
        assert len(data) == 256
        paths = self._paths_from_block_num(block_num)
        for path in paths[1:]: # don't check data subdir
            if not os.path.isdir(path):
                os.mkdir(path)
        path = paths[-1] # may be data subdir, if only 1 block
        file_utils.remove_all(path)
        if any(data):
            for idx, item in enumerate(base_utils.chunk(data, 16)):
                if not any(item): continue
                item_str = "+" + base_utils.list_to_base64(
                    base_utils.encode(idx, item))
                file_utils.touch(os.path.join(path, item_str))
        else:
            for path in reversed(paths[1:]): # don't try to delete data subdir
                subdirs = os.listdir(path)
                if subdirs: break
                os.rmdir(path)

    # read/write for arbitrary data and location
    # Note: We use outfile and infile here, as opposed to returning data
    # in a list, to allow for streaming reads/writes. This is good when
    # the data is long enough that we don't want to store it all into memory

    def read_all(self, offset, length, outfile):
        """
        Reads `length` bytes, starting `offset` bytes into the file

        Output is done using the `write` method on `outfile`, to avoid
        unnecessarily keeping data in memory.

        Returns the number of bytes read.
        """
        if offset + length > self.size:
            length = self.size - offset
        left = length
        tot_amt = 0
        while left:
            mod = offset % 256
            block = self.read_block(offset / 256)
            amt = min(left, 256 - mod) # usually 256
            outfile.write("".join(chr(c) for c in block[mod:mod+amt]))
            tot_amt += amt
            offset += amt
            left -= amt
        return tot_amt

    def write_all(self, offset, length, infile):
        """
        Writes `length` bytes, starting `offset` bytes into the file

        Input is done using the `read` method on `infile`, to avoid
        unnecessarily keeping data in memory.

        Returns the number of bytes written.
        """
        if length is not None: left = length
        tot_amt = 0
        while True:
            mod = offset % 256
            if length is None:
                amt = 256 - mod
            else:
                amt = min(left, 256 - mod) # usually 256
            read_data = [ord(c) for c in infile.read(amt)]
            act_amt = len(read_data)
            if act_amt == 0: break
            self.resize(max(self.size, offset + act_amt))
            if act_amt < 256:
                block = self.read_block(offset / 256)
                block[mod:mod+act_amt] = read_data
            else:
                block = read_data
            self.write_block(offset / 256, block)
            tot_amt += act_amt
            offset += act_amt
            if length is not None:
                left -= act_amt
                if not left: break
        return tot_amt
