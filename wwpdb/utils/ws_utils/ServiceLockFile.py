##
# File: ServiceLockFile.py
# Date: 21-Feb-2012  John Westbrook
#
# Update:
#      02-Aug-2016  jdw adapt for service application -  add logging -
#      14-Mar02017  jdw log aquire timeout
#
##
"""
Class implementing a cross-platform file locking strategy using an auxiliary lock file.

"""

import os
import time
import errno
import logging

logger = logging.getLogger()


class LockFileTimeoutException(Exception):
    pass


class ServiceLockFile(object):
    """A simple cross-platform file locking utilitiy class using an auxiliary
    lock file.

    This class provides internal methods supporting context-management
    (e.g. with statement support).  For example,

    with ServiceLockFile("target-file.db", timeoutSeconds=2) as lock:
        # - process/update the target-file.db.

    # - At the end of this 'with' clause the lock is automatically removed.

    """

    def __init__(self, filePath, timeoutSeconds=15, retrySeconds=0.2):
        """Prepare the file locker. Specify the file to lock and optionally
        the maximum timeoutSeconds and the retrySeconds between each attempt to lock.

        It is assumed that the locking file will be created within the
        path of the target file.
        """
        self.__isLocked = False
        self.__lockFilePath = os.path.join(filePath + ".lock")
        self.__filePath = filePath
        #
        self.__timeoutSeconds = timeoutSeconds
        self.__retrySeconds = retrySeconds
        self.__debug = True
        self.__fd = None
        #

    def acquire(self):
        """Create the lock if no lock file exists.  If a lockfile exists then
        repeat the test every retrySeconds.

        If the lock cannot be acquired within  'timeoutSeconds' then
        throw an exception.

        """
        timeBegin = time.time()
        while True:
            try:
                self.__fd = os.open(self.__lockFilePath, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                if self.__debug:
                    logger.debug("Lock file created %s", self.__lockFilePath)
                break
            except OSError as myErr:
                if myErr.errno != errno.EEXIST:
                    # pass on some unanticipated problem ---
                    raise
                # handle timeout and retry -
                if (time.time() - timeBegin) >= self.__timeoutSeconds:
                    logger.debug("ServiceLockfile(acquire) Failed to acquire lock within timeout %r", self.__timeoutSeconds)
                    raise LockFileTimeoutException("ServiceLockFile(acquire) Internal timeout of %d (seconds) exceeded for %s" % (self.__timeoutSeconds, self.__filePath))
                if self.__debug:
                    logger.debug("Lock file retry for file %s", self.__lockFilePath)
                time.sleep(self.__retrySeconds)
        #
        self.__isLocked = True

    def release(self):
        """Remove any existing lock file."""
        if self.__isLocked:
            os.close(self.__fd)
            os.unlink(self.__lockFilePath)
            self.__isLocked = False
            if self.__debug:
                logger.debug("LockFile(release) removed lock file %s", self.__lockFilePath)

    def __enter__(self):
        """Internal method invoked at the beginning of a 'with' clause."""
        if not self.__isLocked:
            self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Internal method invoked at the end of a 'with' clause."""
        if self.__isLocked:
            self.release()

    def __del__(self):
        """Internal method to cleanup any lingering lock file."""
        self.release()


if __name__ == "__main__":
    pass
