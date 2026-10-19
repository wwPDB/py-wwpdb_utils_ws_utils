##
# File: ServiceLockFileTests.py
# Date:  17-Oct-2026
#
# Updates:
##
"""
Test cases for ServiceLockFile class --

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""

__docformat__ = "restructuredtext en"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import errno
import logging
import os
import tempfile
import unittest
from unittest import mock

from wwpdb.utils.ws_utils.ServiceLockFile import LockFileTimeoutException, ServiceLockFile

logging.basicConfig(level=logging.DEBUG, format="\n[%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logging.getLogger().setLevel(logging.INFO)


class ServiceLockFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpdir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.__target = os.path.join(self.__tmpdir.name, "target.db")
        self.__lockPath = self.__target + ".lock"

    def tearDown(self) -> None:
        self.__tmpdir.cleanup()

    def testAcquireRelease(self) -> None:
        lck = ServiceLockFile(self.__target)
        lck.acquire()
        self.assertTrue(os.path.exists(self.__lockPath))
        lck.release()
        self.assertFalse(os.path.exists(self.__lockPath))
        # Second release is harmless
        lck.release()

    def testContextManager(self) -> None:
        with ServiceLockFile(self.__target, timeoutSeconds=1) as lck:
            self.assertIsInstance(lck, ServiceLockFile)
            self.assertTrue(os.path.exists(self.__lockPath))
        self.assertFalse(os.path.exists(self.__lockPath))

    def testContextManagerPreLocked(self) -> None:
        lck = ServiceLockFile(self.__target)
        lck.acquire()
        # Entering when already locked does not attempt to reacquire
        with lck:
            self.assertTrue(os.path.exists(self.__lockPath))
        self.assertFalse(os.path.exists(self.__lockPath))

    def testTimeout(self) -> None:
        with ServiceLockFile(self.__target):
            lck2 = ServiceLockFile(self.__target, timeoutSeconds=0.3, retrySeconds=0.1)
            with self.assertRaises(LockFileTimeoutException):
                lck2.acquire()
        self.assertFalse(os.path.exists(self.__lockPath))

    def testRetrySucceeds(self) -> None:
        lck1 = ServiceLockFile(self.__target)
        lck1.acquire()
        lck2 = ServiceLockFile(self.__target, timeoutSeconds=5, retrySeconds=0.1)

        # Release the first lock during the retry sleep of the second
        def releaseFirst(_secs: float) -> None:
            lck1.release()

        with mock.patch("wwpdb.utils.ws_utils.ServiceLockFile.time.sleep", side_effect=releaseFirst) as mSleep:
            lck2.acquire()
        self.assertEqual(mSleep.call_count, 1)
        self.assertTrue(os.path.exists(self.__lockPath))
        lck2.release()
        self.assertFalse(os.path.exists(self.__lockPath))

    def testUnexpectedOSError(self) -> None:
        lck = ServiceLockFile(self.__target)
        with mock.patch(
            "wwpdb.utils.ws_utils.ServiceLockFile.os.open", side_effect=OSError(errno.EACCES, "denied")
        ), self.assertRaises(OSError) as cm:
            lck.acquire()
        self.assertEqual(cm.exception.errno, errno.EACCES)
        self.assertFalse(os.path.exists(self.__lockPath))

    def testDelReleases(self) -> None:
        lck = ServiceLockFile(self.__target)
        lck.acquire()
        self.assertTrue(os.path.exists(self.__lockPath))
        del lck
        self.assertFalse(os.path.exists(self.__lockPath))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
