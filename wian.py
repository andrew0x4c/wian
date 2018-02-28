#!/usr/bin/python

# Copyright (c) Andrew Li 2018. This file is licensed under the GPLv3.
# See https://github.com/andrew0x4c/wian for more information,
# including the full LICENSE file.

import os
import sys
import argparse
from wianfile import WIANFile

def run_cat(args):
    f = WIANFile(args.datadir)
    f.read_all(args.offset, f.size, args.outfile)

def run_create(args):
    f = WIANFile(args.datadir, create=True)
    f.write_all(0, None, args.infile)

def run_append(args):
    f = WIANFile(args.datadir)
    f.write_all(f.size, None, args.infile)

def run_resize(args):
    f = WIANFile(args.datadir)
    f.resize(args.size)

parser = argparse.ArgumentParser(
    description="What's in a name? Storing data in file and directory names",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
subparsers = parser.add_subparsers(help="command to run")

def add_datadir_arg(parser):
    # this one is going to be very common, so put it in a function
    parser.add_argument("datadir", metavar="datadir",
        type=str,
        help="the input WIAN directory tree")

def add_outfile_arg(parser):
    # also this one too
    parser.add_argument("outfile", metavar="outfile", nargs="?",
        type=argparse.FileType('wb'), default=sys.stdout,
        help="the output file, or stdout if omitted")

def add_infile_arg(parser):
    # also this one too
    parser.add_argument("infile", metavar="infile", nargs="?",
        type=argparse.FileType('rb'), default=sys.stdin,
        help="the input file, or stdin if omitted")

parse_cat = subparsers.add_parser("cat")
add_datadir_arg(parse_cat)
add_outfile_arg(parse_cat)
parse_cat.add_argument("--offset", dest="offset", metavar="offset",
    action="store", type=int, default=0,
    help="offset to start reading at (default 0)")
parse_cat.set_defaults(func=run_cat)

parse_create = subparsers.add_parser("create")
add_datadir_arg(parse_create)
add_infile_arg(parse_create)
parse_create.set_defaults(func=run_create)

parse_append = subparsers.add_parser("append")
add_datadir_arg(parse_append)
add_infile_arg(parse_append)
parse_append.set_defaults(func=run_append)

parse_resize = subparsers.add_parser("resize")
add_datadir_arg(parse_resize)
parse_resize.add_argument("size", metavar="size",
    action="store", type=int,
    help="the new size, in bytes")
parse_resize.set_defaults(func=run_resize)

args = parser.parse_args()

args.func(args)
