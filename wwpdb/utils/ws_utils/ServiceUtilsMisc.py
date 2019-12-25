##
# File: ServiceUtilsMisc.py
# Date:  7-Aug-2016  John Westbrook
#
# Update:
#
##
"""
Utility functions supporting web service classes.

"""

import hashlib

import logging

logger = logging.getLogger(__name__)


def getMD5(path, block_size=4096, hr=True):
    """
    Chunked MD5 function -

    Block size directly depends on the block size of your filesystem
    to avoid performances issues

    Linux Ext4 block size
        sudo /sbin/blockdev --getbsz /dev/sda1
        > Block size:               4096

    """
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            md5.update(chunk)
    if hr:
        return md5.hexdigest()
    return md5.digest()
