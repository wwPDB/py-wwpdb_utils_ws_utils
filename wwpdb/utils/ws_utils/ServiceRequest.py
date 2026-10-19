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


import contextlib
import logging
import os
import sys
from typing import IO, Any, Dict, List, Optional

try:
    import json
except ImportError:
    import simplejson as json  # type: ignore[no-redef]

from wwpdb.utils.ws_utils.ServiceSessionFactory import ServiceSessionFactory

logger = logging.getLogger()


class ServiceRequestBase:
    """Base container and accessors for input and output parameters and control information."""

    def __init__(self, paramDict: Optional[Dict[str, List[Any]]] = None) -> None:
        #
        #  Input and storage model is dictionary of lists (e.g. dict[myKey] = [,,,])
        #  Single values are stored in the leading element of the list (e.g. dict[myKey][0])
        #
        if paramDict is None:
            paramDict = {}
        self.__dict = paramDict

    def __outputList(self) -> List[str]:
        sL: List[str] = []
        sL.append(" ++Service request contents:\n")
        for k, vL in self.__dict.items():
            sL.append("     - Key: %-35s  value(s): %r" % (k, vL))
        return sL

    def __str__(self) -> str:
        try:
            return "\n  ".join(self.__outputList())
        except:  # noqa: E722 pylint: disable=bare-except
            return ""

    def __repr__(self) -> str:
        return self.__str__()

    def printIt(self, ofh: IO[str] = sys.stdout) -> None:
        with contextlib.suppress(Exception):
            ofh.write("%s" % self.__str__())  # noqa: PLC2801

    def dump(
        self,
        format: str = "text",  # noqa: A002,ARG002  pylint: disable=unused-argument,redefined-builtin
    ) -> Optional[str]:
        try:
            return "\n   ".join(self.__outputList())
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return None

    def getJSON(self) -> str:
        return json.dumps(self.__dict)

    def setJSON(self, JSONString: str) -> None:
        self.__dict = json.loads(JSONString)

    def getValue(self, myKey: str) -> str:
        return self._getStringValue(myKey)

    def getValueOrDefault(self, myKey: str, default: str = "") -> str:
        if not self.exists(myKey):
            return default
        v = self._getStringValue(myKey)
        if len(v) < 1:
            return default
        return v

    def getValueList(self, myKey: str) -> List[Any]:
        return self._getStringList(myKey)

    def getRawValue(self, myKey: str) -> Any:
        return self._getRawValue(myKey)

    def getDictionary(self) -> Dict[str, List[Any]]:
        return self.__dict

    def setValue(self, myKey: str, aValue: Any) -> bool:
        try:
            self.__dict[myKey] = [aValue]
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def setValueList(self, myKey: str, valueList: List[Any]) -> bool:
        try:
            self.__dict[myKey] = valueList
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def setDictionary(self, myDict: Dict[str, Any], overWrite: bool = False) -> bool:
        for k, v in myDict.items():
            if overWrite or (not self.exists(k)):
                self.setValue(k, v)
        return True

    def exists(self, myKey: str) -> bool:
        try:
            return myKey in self.__dict
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def _getRawValue(self, myKey: str) -> Any:
        try:
            return self.__dict[myKey][0]
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def _getStringValue(self, myKey: str) -> str:
        try:
            return str(self.__dict[myKey][0]).strip()
        except:  # noqa: E722 pylint: disable=bare-except
            return ""

    def _getIntegerValue(self, myKey: str) -> Optional[int]:
        try:
            return int(self.__dict[myKey][0])
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def _getDoubleValue(self, myKey: str) -> Optional[float]:
        try:
            return float(self.__dict[myKey][0])
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def _getStringList(self, myKey: str) -> List[Any]:
        try:
            return self.__dict[myKey]
        except:  # noqa: E722 pylint: disable=bare-except
            return []


class ServiceRequest(ServiceRequestBase):
    def __init__(self, paramDict: Optional[Dict[str, List[Any]]]) -> None:
        super(ServiceRequest, self).__init__(paramDict)
        self.__returnFormatDefault = ""
        self.__requestPrefix = ""

    def setDefaultReturnFormat(self, return_format: str = "html") -> None:
        self.__returnFormatDefault = return_format
        if not self.exists("return_format"):
            self.setValue("return_format", self.__returnFormatDefault)

    def setRequestPathPrefix(self, prefix: str) -> None:
        """Set optional request path prefix to be removed before applying application routing."""
        self.__requestPrefix = prefix

    def getRequestPathPrefix(self) -> str:
        """Get request path prefix."""
        return self.__requestPrefix

    def getRequestPath(self) -> Optional[str]:
        try:
            iRp = self._getStringValue("request_path")
            if len(self.__requestPrefix) > 0:
                if iRp.startswith(self.__requestPrefix):
                    rp = iRp[len(self.__requestPrefix) :]
                    return rp
                return iRp
            return iRp
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Request path processing FAILED")

        return None

    def getReturnFormat(self) -> str:
        if not self.exists("return_format"):
            self.setValue("return_format", self.__returnFormatDefault)
        return self._getStringValue("return_format")

    def setReturnFormat(self, return_format: str = "json") -> bool:
        return self.setValue("return_format", return_format)

    def getSessionId(self) -> str:
        return self._getStringValue("session_id")

    def getTopSessionPath(self) -> str:
        return self._getStringValue("top_session_path")

    def getServiceUserId(self) -> str:
        return self._getStringValue("service_user_id")

    def setServiceUserId(self, serviceUserId: str) -> bool:
        try:
            return self.setValue("service_user_id", serviceUserId)
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def getSessionUserPath(self) -> str:
        return self._getStringValue("session_user_path")

    def setTopSessionPath(self, pth: str) -> bool:
        try:
            return self.setValue("top_session_path", pth)
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def setSiteId(self, siteId: str) -> bool:
        try:
            self.setValue("wwpdb_site_id", siteId)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return False

    def getSiteId(self) -> str:
        return self._getStringValue("wwpdb_site_id")

    def getSessionPath(self) -> str:
        return os.path.join(self._getStringValue("top_session_path"), "sessions")

    def getSemaphore(self) -> str:
        return self._getStringValue("semaphore")

    def getSessionObj(self, new: bool = False) -> ServiceSessionFactory:
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
            elif self.exists("session_id"):
                logger.debug("Aquiring existing session %s ", self._getStringValue("session_id"))
                sObj.setId(uid=self._getStringValue("session_id"))
            self.setValue("session_user_path", sObj.getSessionUserPath())
            logger.debug("Completed")
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Session acquisition/creation FAILING")

        return sObj
