##
# File:    ServiceSessionFactory.py
# Date:    6-Jul-2016 J. Westbrook
#
# Updates:
##
"""
Utilities for service session directory management.

"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import hashlib
import logging
import os.path
import shutil
import time
from typing import Optional

logger = logging.getLogger()


class ServiceSessionFactory:
    """
    Utilities for service session directory management.

    """

    def __init__(self, topPath: Optional[str] = None, serviceUserId: Optional[str] = None) -> None:
        """
        Organization of the service session directory is --

        <topPath>/<Service_id>/<sha-hash>/<session_files>

        Parameters:
        :param string topPath: is the path to the directory containing the hash-id sub-directory.
        :param string serviceId: is the path to the directory containing the hash-id sub-directory.

        """
        self.__topSessionPath = topPath or "."
        self.__serviceUserId = serviceUserId or "ANONYMOUS"
        self.__uid: Optional[str] = None

    def __str__(self) -> str:
        return "Session top path: %s\nService user id: %s\nUnique identifier: %s\nSession path: %s\n" % (
            self.__topSessionPath,
            self.__serviceUserId,
            self.__uid,
            self.getPath(),
        )

    def __repr__(self) -> str:
        return self.__str__()

    def setId(self, uid: Optional[str]) -> bool:
        self.__uid = uid
        return True

    def getId(self) -> Optional[str]:
        return self.__uid

    def assignId(self) -> str:
        uid = hashlib.sha1(repr(time.time()).encode("utf-8")).hexdigest()  # noqa: S324
        self.__uid = uid
        return uid

    def __getPath(self, relative: bool = False) -> Optional[str]:
        pth: Optional[str] = None
        if self.__uid is None:
            return pth
        try:
            if relative:
                pth = os.path.join("/sessions", self.__serviceUserId, self.__uid)
            else:
                pth = os.path.join(self.__topSessionPath, "sessions", self.__serviceUserId, self.__uid)
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILING")
            pth = None

        return pth

    def getPath(self) -> Optional[str]:
        try:
            pth = self.__getPath()
            logger.debug("Session path %r", pth)
            if pth is not None and os.access(pth, os.F_OK):
                return pth
            return None
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILING")

        return None

    def getRelativePath(self) -> Optional[str]:
        return self.__getPath(relative=True)

    def getTopPath(self) -> str:
        return self.__topSessionPath

    def getSessionUserPath(self) -> str:
        return os.path.join(self.__topSessionPath, "sessions", self.__serviceUserId)

    def setTopPath(self, topSessionPath: str) -> bool:
        self.__topSessionPath = topSessionPath
        return True

    def getTopSessionPath(self) -> str:
        return self.__topSessionPath

    def setTopSessionPath(self, topSessionPath: str) -> bool:
        self.__topSessionPath = topSessionPath
        return True

    def setServiceUserId(self, serviceUserId: str) -> bool:
        self.__serviceUserId = serviceUserId
        return True

    def makeSessionPath(self) -> Optional[str]:
        """If the path to the current session directory does not exist
        create it and return the session path.
        """
        try:
            pth = self.__getPath()
            if pth is None:
                return None
            if not os.access(pth, os.F_OK):
                os.makedirs(pth)
            return pth
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def remakeSessionPath(self) -> Optional[str]:
        try:
            pth = self.__getPath()
            if pth is None:
                return None
            if os.access(pth, os.F_OK):
                shutil.rmtree(pth, True)
            os.makedirs(pth)
            return pth
        except:  # noqa: E722 pylint: disable=bare-except
            return None
