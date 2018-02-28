# WIAN (what's in a name?)
What's in a name? Storing data in file and directory names

Are your files using up too much space? Use WIAN to store everything in 0 bytes! The ultimate compression algorithm!

(Here the example was run on macOS)

    $ head -c 1048576 /dev/urandom > rand
    $ md5 rand
    MD5 (rand) = 11fb195f6fa6135a8155134c996fea40  rand
    $ du -sh rand
    1.0M    rand
    $ python wian.py create randdir rand
    $ rm rand
    $ du -sh randdir
      0B    randdir
    $ python wian.py cat randdir rand
    $ md5 rand
    MD5 (rand) = 11fb195f6fa6135a8155134c996fea40  rand
    $

(Using `randdir` was enough to reconstruct `rand` - WIAN doesn't try to "hide" the data elsewhere.)


## Pronouncation

WIAN rhymes with cyan.


## Running

    [python] wian.py cat mydir [outfile] [--offset num]
    [python] wian.py create mydir [infile]
    [python] wian.py append mydir [infile]
    [python] wian.py resize mydir num

If input/output files are omitted, stdin and stdout are used when appropriate.


## Example

Example session, demonstrating some of the options

(Here the example was run on macOS)

    $ cat hello.txt
    Hello, World!
    $ du -sh hello.txt
    4.0K    hello.txt
    $ python wian.py create hello hello.txt
    $ rm hello.txt
    $ du -sh hello
      0B    hello
    $ python wian.py cat hello
    Hello, World!
    $ python wian.py append hello
    test
    $ du -sh hello
      0B    hello
    $ python wian.py cat hello
    Hello, World!
    test
    $ python wian.py resize hello 5
    $ python wian.py cat hello
    Hello$


## Why?

On the computers in our computer lab, we have a relatively small disk quota (2GB). However, I noticed that directories and empty files do not count against the quota. This gave me the idea of storing data without actually having data inside a file - using only filenames and other metadata.


## How?

One naive approach would be to store each byte or block of bytes as the file name of an empty file. However, this doesn't preserve order (without extra data like the modification time), and doesn't allow for multiple occurrences of a byte/block. The next idea might be to prepend the index of the byte/block before its value. This solves the problems of order and duplicates, but still does not work when certain bytes are not allowed in filenames, such as `/`. Thus, the algorithm needs some method of safely encoding the data, but after adding all this, the algorithm would actually work.

At this point, we can correctly store and retrieve data. However, if the original file is large, the directory will contain a large number of files, which may be difficult or very slow to use, especially when just a few bytes are needed (the program would need to loop through all filenames every time). To avoid this, we store the blocks in a tree (made of directories), where each node contains either blocks of data or more nodes. Now, given a block number, we can quickly find the data stored there. This necessitates extra logic for growing/shrinking the tree when the file grows/shrinks enough.

This method of storing data in a tree is very similar to how filesystems store data. If you have worked with filesystems before, some of the ideas used here may be familiar.


## Future work

Write WIAN as a FUSE driver! This way you could mount a filesystem which automatically stores files in the WIAN format, and have programs interact with them as if they were real files, while appearing to use no space at all.


## License

Licensed under GPLv3. See the LICENSE file for details.

Copyright (c) Andrew Li 2018
