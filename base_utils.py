# Copyright (c) Andrew Li 2018. This file is licensed under the GPLv3.
# See https://github.com/andrew0x4c/wian for more information,
# including the full LICENSE file.

# Just some utility functions for lists and base conversion

import string

def chunk(xs, size):
    return [xs[i:i+size] for i in range(0, len(xs), size)]

# Convert a 1-hex digit index and 32-hex digit data into 22 base-64 digits

def encode(idx, data):
    # 8 -> 4
    data = [(x >> shift) & 0xF for x in data for shift in (4, 0)]
    # merge
    data = [idx] + data
    # 4 -> 12
    data = [(h1 << 8) | (h2 << 4) | h3 for h1, h2, h3 in chunk(data, 3)]
    # 12 -> 6
    data = [(x >> shift) & 0x3F for x in data for shift in (6, 0)]
    return data

# Convert 22 base-64 digits into a 1-hex digit index and 32-hex digit data

def decode(data):
    # 6 -> 12
    data = [(n1 << 6) | n2 for n1, n2 in chunk(data, 2)]
    # 12 -> 4
    data = [(x >> shift) & 0xF for x in data for shift in (8, 4, 0)]
    # unmerge
    idx, data = data[0], data[1:]
    # 4 -> 8
    data = [(h1 << 4) | h2 for h1, h2 in chunk(data, 2)]
    return idx, data

def to_base(num, base):
    result = []
    while num:
        digit = num % base
        num /= base
        result.insert(0, digit)
    return result

def to_base_pad(num, base, length):
    # this also computes the modulo
    result = []
    for _ in range(length):
        digit = num % base
        num /= base
        result.insert(0, digit)
    return result

def from_base(num, base):
    result = 0
    for x in num:
        result = result * base + x
    return result

def num_hex_needed(num):
    # how many hex digits are needed to represent the number
    # useful for finding the depth of the data tree
    curr = 0
    while 1 << (curr * 4) < num: curr += 1
    return curr

# we don't use the base64 module because we need to deal with
# fractions of bytes
# also, I like having the 0 digit corresponding to the 0 character;
# base64 is more commonly A-Za-z0-9+/ (or -_), but here we use 0-9A-Za-z-_
_num_to_b64char = (
    string.digits + string.ascii_uppercase + string.ascii_lowercase + "-_"
)
_b64char_to_num = {char: i for i, char in enumerate(_num_to_b64char)}

def list_to_base64(nums):
    return "".join([_num_to_b64char[x] for x in nums])

def base64_to_list(s):
    return [_b64char_to_num[c] for c in s]
