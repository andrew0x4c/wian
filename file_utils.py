# Copyright (c) Andrew Li 2018. This file is licensed under the GPLv3.
# See https://github.com/andrew0x4c/wian for more information,
# including the full LICENSE file.

# Just some utility functions for filesystem level operations

import os

def touch(path):
    with open(path, 'wb'): pass

def remove_all(path):
    item_strs = os.listdir(path)
    for item_str in item_strs:
        os.remove(os.path.join(path, item_str))

def remove_all_recursive(path):
    item_strs = os.listdir(path)
    for item_str in item_strs:
        item_str_path = os.path.join(path, item_str)
        if os.path.isdir(item_str_path):
            remove_all_recursive(item_str_path)
            os.rmdir(item_str_path)
        else:
            os.remove(item_str_path)

def remove_recursive(path):
    if os.path.isdir(path):
        remove_all_recursive(path)
        os.rmdir(path)
    else:
        os.remove(path)
