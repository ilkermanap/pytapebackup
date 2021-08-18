# pytapebackup

Library and applications for managing backups to tape.

## Devices

This library will try to use tape devices listed at /dev directory. For linux, this will be
/dev/stX  /dev/nstX, for Freebsd, /dev/saX   /dev/nsaX.

Library depends on the operating system for accessing the tape through device files.
Positioning on tape requires mt utility.


## Tape Structure

    tape id| tarfile1 | tarfile1.properties | .... | tarfileN | tarfileN.properties

Each new tape will have a tape id as a tar file as the first record. This tar
file will include only one file with a uuid inside.

Next block on tape will be a new tar file with the files backed up.

Next block after the tar file will have the information related to previous block.
An sqlite database with records related to previous block.

When a new tape read, we will read the first block. This block will give us the
tape label, when it is first created, etc.

Then we will read blocks by skipping the  blocks with actual files,  and reading the
blocks that includes information about backups. This approach will be faster than trying
to run "tar tvf /dev/st0" because we will only retrieve relatively very small archives then
the actual backups.

