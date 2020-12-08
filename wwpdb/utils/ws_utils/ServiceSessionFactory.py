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
import time
import os.path
import shutil
import logging

logger = logging.getLogger()


class ServiceSessionFactory(object):
    """
    Utilities for service session directory management.

    """

    def __init__(self, topPath=None, serviceUserId=None):
        """
        Organization of the service session directory is --

        <topPath>/<Service_id>/<sha-hash>/<session_files>

        Parameters:
        :param string topPath: is the path to the directory containing the hash-id sub-directory.
        :param string serviceId: is the path to the directory containing the hash-id sub-directory.

        """
        self.__topSessionPath = topPath if topPath else "."
        self.__serviceUserId = serviceUserId if serviceUserId else "ANONYMOUS"
        self.__uid = None

    def __str__(self):
        return "Session top path: %s\nService user id: %s\nUnique identifier: %s\nSession path: %s\n" % (self.__topSessionPath, self.__serviceUserId, self.__uid, self.getPath())

    def __repr__(self):
        return self.__str__()

    def setId(self, uid):
        self.__uid = uid
        return True

    def getId(self):
        return self.__uid

    def assignId(self):
        self.__uid = hashlib.sha1(repr(time.time()).encode("utf-8")).hexdigest()
        return self.__uid

    def __getPath(self, relative=False):
        pth = None
        try:
            if relative:
                pth = os.path.join("/sessions", self.__serviceUserId, self.__uid)
            else:
                pth = os.path.join(self.__topSessionPath, "sessions", self.__serviceUserId, self.__uid)
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILING")
            pth = None

        return pth

    def getPath(self):
        try:
            pth = self.__getPath()
            logger.debug("Session path %r", pth)
            if os.access(pth, os.F_OK):
                return pth
            else:
                return None
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILING")

        return None

    def getRelativePath(self):
        return self.__getPath(relative=True)

    def getTopPath(self):
        return self.__topSessionPath

    def getSessionUserPath(self):
        return os.path.join(self.__topSessionPath, "sessions", self.__serviceUserId)

    def setTopPath(self, topSessionPath):
        self.__topSessionPath = topSessionPath
        return True

    def getTopSessionPath(self):
        return self.__topSessionPath

    def setTopSessionPath(self, topSessionPath):
        self.__topSessionPath = topSessionPath
        return True

    def setServiceUserId(self, serviceUserId):
        self.__serviceUserId = serviceUserId
        return True

    def makeSessionPath(self):
        """If the path to the current session directory does not exist
        create it and return the session path.
        """
        try:
            pth = self.__getPath()
            if not os.access(pth, os.F_OK):
                os.makedirs(pth)
            return pth
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def remakeSessionPath(self):
        try:
            pth = self.__getPath()
            if os.access(pth, os.F_OK):
                shutil.rmtree(pth, True)
            os.makedirs(pth)
            return pth
        except:  # noqa: E722 pylint: disable=bare-except
            return None
