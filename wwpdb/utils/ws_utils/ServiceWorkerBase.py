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
import time

# import types
# import string
# import traceback
# import ntpath

import logging

#
from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.ws_utils.ServiceDataStore import ServiceDataStore

from wwpdb.utils.ws_utils.ServiceSessionState import ServiceSessionState
from wwpdb.utils.ws_utils.ServiceHistory import ServiceHistory

#
logger = logging.getLogger()


class ServiceWorkerBase(object):
    def __init__(self, reqObj=None, sessionDataPrefix=None):
        """
        Base class supporting web application worker methods.

        Performs URL -> application mapping for this module.

        """
        self._reqObj = reqObj
        self._sObj = None
        self._sessionId = None
        self._sessionPath = None
        self._rltvSessionPath = None
        #
        #
        self._siteId = self._reqObj.getSiteId()
        self._cI = ConfigInfo(self._siteId)
        #
        #  ServiceDataStore prefix for general session data -- used by _getSession()
        self._sdsPrefix = sessionDataPrefix if sessionDataPrefix else "general"
        self._sds = None
        #
        # Service items include:
        # self.__class__.__name__,sys._getframe().f_code.co_name
        self.__appPathD = {}
        #

    def _trackServiceStatus(self, op, **params):
        """Add a service history status tracking record.

        :param string  op:  operation status  (e.g., 'created', 'submitted', 'completed', 'failed' , ...)
        :param dictionary params:  optional key-value payload stored with status record.

        """
        if params and "remote_addr" not in params:
            params["remote_addr"] = self._reqObj.getValue("remote_addr")
        #
        sH = ServiceHistory(historyPath=self._reqObj.getSessionUserPath())
        return sH.add(sessionId=self._sessionId, statusOp=op, **params)

    def _getServiceActivitySummary(self):
        """Get the service activity summary."""
        sH = ServiceHistory(historyPath=self._reqObj.getSessionUserPath())
        return sH.getActivitySummary()

    def addService(self, url, opName):
        self.__appPathD[url] = opName

    def addServices(self, serviceDict):
        for k, v in serviceDict.items():
            self.__appPathD[k] = v

    def _run(self, reqPath=None):
        """Map operation to path and invoke operation.  Exceptions are caught within this method.

        :returns:

        Operation output is packaged in a ServiceSessionState() object.

        """
        #
        requestPath = None
        try:
            requestPath = reqPath if reqPath else self._reqObj.getRequestPath()
            #
            if requestPath not in self.__appPathD:
                # bail out if operation is unknown -
                sst = ServiceSessionState()
                sst.setServiceError(msg="Unknown operation")
            else:
                mth = getattr(self, self.__appPathD[requestPath], None)
                sst = mth()
            return sst
        except:  # noqa: E722 pylint: disable=bare-except
            logging.exception("FAILING for requestPath %r ", requestPath)
            sst = ServiceSessionState()
            sst.setServiceError(msg="Operation failure")

        return sst

    #
    def _appendSessionStore(self, iD=None):
        """Dictionary of key value pairs will be appended to the session parameter store.

        list and dict type values are extended/appended to existing values of corresponding types.


        """
        try:
            if iD is not None and isinstance(iD, dict) and len(iD) > 0:
                self._sds.update(iD)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            logging.exception("FAILED updating with input %r ", iD)
        return False

    def _getSessionStoreDict(self):
        """Recover session store data as a dictionary."""
        try:
            return self._sds.getDictionary()
        except:  # noqa: E722 pylint: disable=bare-except
            logging.exception("FAILED to recover session store")

        return {}

    def _setSessionStoreValue(self, ky, val):
        """Set session store data as a dictionary."""
        try:
            return self._sds.set(ky, val)
        except:  # noqa: E722 pylint: disable=bare-except
            logging.exception("FAILED to set session store value")

        return {}

    def _trackSessionHistory(self, msg="ok"):
        rP = self._reqObj.getRequestPath()
        tS = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
        self._sds.append("session_history", (rP, tS, msg))

    def _getSession(self, new=False, useContext=False, contextOverWrite=True, trackHistory=True):
        """Join existing session or create new session as required."""
        #
        try:
            #
            self._sObj = self._reqObj.getSessionObj(new=new)
            self._sessionId = self._sObj.getId()
            self._sessionPath = self._sObj.getPath()
            logging.debug("session   id  %s", self._sessionId)
            logging.debug("session path  %s", self._sessionPath)
            if self._sessionPath is None:
                return False
            self._rltvSessionPath = self._sObj.getRelativePath()
            self._sds = ServiceDataStore(sessionPath=self._sessionPath, prefix=self._sdsPrefix)
            if useContext and not new:
                dd = self._getSessionStoreDict()
                logging.debug("Imported %r", dd)
                self._reqObj.setDictionary(dd, overWrite=contextOverWrite)
            if trackHistory:
                self._trackSessionHistory(msg="begins")
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            logging.exception("FAILING create or joining session")
        return False

    ##
