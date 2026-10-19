##
# File:  ServiceWorkerBase.py
# Date:  7-July-2016
#
# Updates:
#    22-Sep-2016  jdw add session tracking
#    26-Sep-2016  jdw add _getServiceTrackingSummary()
#     2-Dec-2016  jdw include remote_addr in all tracking records.
#    18-Feb-2017  jdw use internal method to obtain siteId.
#    15-Mar-2017  jdw add trackHistory=True to _getSession()
##
"""
Base class for supporting web service processing modules.

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) wwPDB

"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

# import os
# import sys
# import types
# import string
# import traceback
# import ntpath
import logging
import time
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from wwpdb.utils.config.ConfigInfo import ConfigInfo

from wwpdb.utils.ws_utils.ServiceDataStore import ServiceDataStore
from wwpdb.utils.ws_utils.ServiceHistory import ServiceHistory
from wwpdb.utils.ws_utils.ServiceRequest import ServiceRequest

if TYPE_CHECKING:
    from wwpdb.utils.ws_utils.ServiceSessionFactory import ServiceSessionFactory
from wwpdb.utils.ws_utils.ServiceSessionState import ServiceSessionState

logger = logging.getLogger()


class ServiceWorkerBase:
    def __init__(self, reqObj: ServiceRequest, sessionDataPrefix: Optional[str] = None) -> None:
        """
        Base class supporting web application worker methods.

        Performs URL -> application mapping for this module.

        """
        self._reqObj = reqObj
        self._sObj: Optional[ServiceSessionFactory] = None
        self._sessionId: Optional[str] = None
        self._sessionPath: Optional[str] = None
        self._rltvSessionPath: Optional[str] = None
        self._siteId = self._reqObj.getSiteId()
        self._cI = ConfigInfo(self._siteId)
        #
        #  ServiceDataStore prefix for general session data -- used by _getSession()
        self._sdsPrefix = sessionDataPrefix or "general"
        self._sds: Optional[ServiceDataStore] = None
        #
        # Service items include:
        # self.__class__.__name__,sys._getframe().f_code.co_name
        self.__appPathD: Dict[str, str] = {}

    def _trackServiceStatus(self, op: str, **params: Any) -> bool:
        """Add a service history status tracking record.

        :param string  op:  operation status  (e.g., 'created', 'submitted', 'completed', 'failed' , ...)
        :param dictionary params:  optional key-value payload stored with status record.

        """
        if params and "remote_addr" not in params:
            params["remote_addr"] = self._reqObj.getValue("remote_addr")
        sH = ServiceHistory(historyPath=self._reqObj.getSessionUserPath())
        return sH.add(sessionId=self._sessionId, statusOp=op, **params)

    def _getServiceActivitySummary(self) -> Dict[str, Any]:
        """Get the service activity summary."""
        sH = ServiceHistory(historyPath=self._reqObj.getSessionUserPath())
        return sH.getActivitySummary()

    def addService(self, url: str, opName: str) -> None:
        self.__appPathD[url] = opName

    def addServices(self, serviceDict: Dict[str, str]) -> None:
        for k, v in serviceDict.items():
            self.__appPathD[k] = v

    def _run(self, reqPath: Optional[str] = None) -> ServiceSessionState:
        """Map operation to path and invoke operation.  Exceptions are caught within this method.

        :returns:

        Operation output is packaged in a ServiceSessionState() object.

        """
        requestPath: Optional[str] = None
        sst: ServiceSessionState
        try:
            requestPath = reqPath or self._reqObj.getRequestPath()
            if requestPath not in self.__appPathD:
                # bail out if operation is unknown -
                sst = ServiceSessionState()
                sst.setServiceError(msg="Unknown operation")
            else:
                # Raises AttributeError (handled below) if the operation method is not defined
                mth = getattr(self, self.__appPathD[requestPath])
                sst = mth()
            return sst
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILING for requestPath %r ", requestPath)
            sst = ServiceSessionState()
            sst.setServiceError(msg="Operation failure")

        return sst

    def _appendSessionStore(self, iD: Optional[Dict[str, Any]] = None) -> bool:
        """Dictionary of key value pairs will be appended to the session parameter store.

        list and dict type values are extended/appended to existing values of corresponding types.


        """
        try:
            if iD is not None and isinstance(iD, dict) and len(iD) > 0:
                self.__getSds().update(iD)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILED updating with input %r ", iD)
        return False

    def _getSessionStoreDict(self) -> Dict[str, Any]:
        """Recover session store data as a dictionary."""
        try:
            return self.__getSds().getDictionary()
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILED to recover session store")

        return {}

    def _setSessionStoreValue(self, ky: str, val: Any) -> Union[bool, Dict[str, Any]]:
        """Set session store data as a dictionary."""
        try:
            return self.__getSds().set(ky, val)
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILED to set session store value")

        return {}

    def _trackSessionHistory(self, msg: str = "ok") -> None:
        rP = self._reqObj.getRequestPath()
        tS = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
        self.__getSds().append("session_history", (rP, tS, msg))

    def __getSds(self) -> ServiceDataStore:
        if self._sds is None:
            emsg = "Session data store is not initialized"
            raise ValueError(emsg)
        return self._sds

    def _getSession(
        self, new: bool = False, useContext: bool = False, contextOverWrite: bool = True, trackHistory: bool = True
    ) -> bool:
        """Join existing session or create new session as required."""
        try:
            self._sObj = self._reqObj.getSessionObj(new=new)
            self._sessionId = self._sObj.getId()
            self._sessionPath = self._sObj.getPath()
            logger.debug("session   id  %s", self._sessionId)
            logger.debug("session path  %s", self._sessionPath)
            if self._sessionPath is None:
                return False
            self._rltvSessionPath = self._sObj.getRelativePath()
            self._sds = ServiceDataStore(sessionPath=self._sessionPath, prefix=self._sdsPrefix)
            if useContext and not new:
                dd = self._getSessionStoreDict()
                logger.debug("Imported %r", dd)
                self._reqObj.setDictionary(dd, overWrite=contextOverWrite)
            if trackHistory:
                self._trackSessionHistory(msg="begins")
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILING create or joining session")
        return False

    ##
