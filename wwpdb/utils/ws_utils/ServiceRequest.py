##
# File:    ServiceRequest.py
# Date:    2-Aug-2016  J. Westbrook
#          Fork of WebRequest adapted for service naming conventions and functions.
# Updated:
#       3-Aug-2016 jdw standardize case for wwpdb_site_id
#      23-Sep-2016 jdw add getSessionUserPath()
##
"""
WebRequest provides containers and accessors for managing request parameter information.

This is an application neutral version shared by UI modules --

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import sys
import os
import logging

try:
    import json
except ImportError:
    import simplejson as json

from wwpdb.utils.ws_utils.ServiceSessionFactory import ServiceSessionFactory

logger = logging.getLogger()


class ServiceRequestBase(object):

    """Base container and accessors for input and output parameters and control information."""

    def __init__(self, paramDict=None):
        #
        #  Input and storage model is dictionary of lists (e.g. dict[myKey] = [,,,])
        #  Single values are stored in the leading element of the list (e.g. dict[myKey][0])
        #
        if paramDict is None:
            paramDict = {}
        self.__dict = paramDict

    def __outputList(self):
        sL = []
        sL.append(" ++Service request contents:\n")
        for k, vL in self.__dict.items():
            sL.append("     - Key: %-35s  value(s): %r" % (k, vL))
        return sL

    def __str__(self):
        try:
            return "\n  ".join(self.__outputList())
        except:  # noqa: E722 pylint: disable=bare-except
            return ""

    def __repr__(self):
        return self.__str__()

    def printIt(self, ofh=sys.stdout):
        try:
            ofh.write("%s" % self.__str__())
        except:  # noqa: E722 pylint: disable=bare-except
            pass

    def dump(self, format="text"):  # pylint: disable=unused-argument,redefined-builtin
        try:
            return "\n   ".join(self.__outputList())
        except:  # noqa: E722 pylint: disable=bare-except
            pass

    def getJSON(self):
        return json.dumps(self.__dict)

    def setJSON(self, JSONString):
        self.__dict = json.loads(JSONString)

    def getValue(self, myKey):
        return self._getStringValue(myKey)

    def getValueOrDefault(self, myKey, default=""):
        if not self.exists(myKey):
            return default
        v = self._getStringValue(myKey)
        if len(v) < 1:
            return default
        return v

    def getValueList(self, myKey):
        return self._getStringList(myKey)

    def getRawValue(self, myKey):
        return self._getRawValue(myKey)

    def getDictionary(self):
        return self.__dict

    #
    def setValue(self, myKey, aValue):
        try:
            self.__dict[myKey] = [aValue]
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def setValueList(self, myKey, valueList):
        try:
            self.__dict[myKey] = valueList
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def setDictionary(self, myDict, overWrite=False):
        for k, v in myDict.items():
            if overWrite or (not self.exists(k)):
                self.setValue(k, v)
        return True

    def exists(self, myKey):
        try:
            return myKey in self.__dict
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    #
    def _getRawValue(self, myKey):
        try:
            return self.__dict[myKey][0]
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def _getStringValue(self, myKey):
        try:
            return str(self.__dict[myKey][0]).strip()
        except:  # noqa: E722 pylint: disable=bare-except
            return ""

    def _getIntegerValue(self, myKey):
        try:
            return int(self.__dict[myKey][0])
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def _getDoubleValue(self, myKey):
        try:
            return float(self.__dict[myKey][0])
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def _getStringList(self, myKey):
        try:
            return self.__dict[myKey]
        except:  # noqa: E722 pylint: disable=bare-except
            return []


class ServiceRequest(ServiceRequestBase):
    def __init__(self, paramDict):
        super(ServiceRequest, self).__init__(paramDict)
        self.__returnFormatDefault = ""
        self.__requestPrefix = ""

    def setDefaultReturnFormat(self, return_format="html"):
        self.__returnFormatDefault = return_format
        if not self.exists("return_format"):
            self.setValue("return_format", self.__returnFormatDefault)

    def setRequestPathPrefix(self, prefix):
        """Set optional request path prefix to be removed before applying application routing."""
        self.__requestPrefix = prefix

    def getRequestPathPrefix(self):
        """Get request path prefix."""
        return self.__requestPrefix

    def getRequestPath(self):
        try:
            iRp = self._getStringValue("request_path")
            if len(self.__requestPrefix) > 0:
                if iRp.startswith(self.__requestPrefix):
                    rp = iRp[len(self.__requestPrefix) :]
                    return rp
                else:
                    return iRp
            else:
                return iRp
        except:  # noqa: E722 pylint: disable=bare-except
            logging.exception("Request path processing FAILED")

        return None

    def getReturnFormat(self):
        if not self.exists("return_format"):
            self.setValue("return_format", self.__returnFormatDefault)
        return self._getStringValue("return_format")

    def setReturnFormat(self, return_format="json"):
        return self.setValue("return_format", return_format)

    def getSessionId(self):
        return self._getStringValue("session_id")

    def getTopSessionPath(self):
        return self._getStringValue("top_session_path")

    def getServiceUserId(self):
        return self._getStringValue("service_user_id")

    def setServiceUserId(self, serviceUserId):
        try:
            return self.setValue("service_user_id", serviceUserId)
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def getSessionUserPath(self):
        return self._getStringValue("session_user_path")

    def setTopSessionPath(self, pth):
        try:
            return self.setValue("top_session_path", pth)
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    #

    def setSiteId(self, siteId):
        try:
            self.setValue("wwpdb_site_id", siteId)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return False

    def getSiteId(self):
        return self._getStringValue("wwpdb_site_id")

    def getSessionPath(self):
        return os.path.join(self._getStringValue("top_session_path"), "sessions")

    def getSemaphore(self):
        return self._getStringValue("semaphore")

    def getSessionObj(self, new=False):
        """Get or create new session -"""
        try:
            logger.debug("Starting")
            sObj = ServiceSessionFactory()
            if self.exists("top_session_path"):
                sObj.setTopSessionPath(topSessionPath=self._getStringValue("top_session_path"))
            if self.exists("service_user_id"):
                sObj.setServiceUserId(serviceUserId=self._getStringValue("service_user_id"))
            if new:
                sObj.assignId()
                sObj.makeSessionPath()
                self.setValue("session_id", sObj.getId())
                logger.debug("Creating new session %s ", sObj.getId())
            else:
                if self.exists("session_id"):
                    logger.debug("Aquiring existing session %s ", self._getStringValue("session_id"))
                    sObj.setId(uid=self._getStringValue("session_id"))
            #
            self.setValue("session_user_path", sObj.getSessionUserPath())
            logger.debug("Completed")
        except:  # noqa: E722 pylint: disable=bare-except
            logging.exception("Session acquisition/creation FAILING")

        return sObj
