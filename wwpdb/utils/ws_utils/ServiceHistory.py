##
# File:  SessionHistory
# Date:  23-Sept-2016
#
# Updated:
#        25-Sep-2016  jdw add activity summary method -
##
"""
Methods to manage service session history tracking  --

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import logging

try:
    import cPickle as pickle
except ImportError:
    import pickle
import os.path
import copy
import time
import datetime
import dateutil.parser

from operator import itemgetter
from wwpdb.utils.ws_utils.ServiceLockFile import ServiceLockFile

logger = logging.getLogger()


class ServiceHistory(object):
    """Methods to manage service session history tracking"""

    #

    def __init__(self, historyPath, useUTC=False):
        """"""
        #
        self.__useUtc = useUTC
        self.__historyPath = historyPath
        self.__filePath = None
        self.__timeOutSeconds = 2.0
        self.__retrySeconds = 0.1
        self.__unlocked_maxretry = 5  # Unlocked status history retrieval return for pickle erro
        self.__unlocked_retrySeconds = 3  # Unlocked status history return sleep
        self.__setup()

    def __setup(self):
        #
        # self.__pickleProtocol = pickle.HIGHEST_PROTOCOL
        self.__pickleProtocol = 0
        try:
            self.__filePath = os.path.join(self.__historyPath, "history-session-store.pic")
            logger.debug("Service history data store path %r", self.__filePath)
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILING for filePath %r", self.__filePath)

    #
    def __serialize(self, iD, mode="wb"):
        """Internal method to write session history data to persistent store."""
        with ServiceLockFile(self.__filePath, timeoutSeconds=self.__timeOutSeconds, retrySeconds=self.__retrySeconds) as lock:  # noqa: F841 pylint: disable=unused-variable
            try:
                with open(self.__filePath, mode) as fb:
                    pickle.dump(iD, fb, self.__pickleProtocol)
                return True
            except:  # noqa: E722 pylint: disable=bare-except
                logger.exception("Serialization failure with file %s", self.__filePath)
        return False

    def __deserialize(self):
        """Internal method to recover session history data from persistent store. Locks file"""
        rD = {}
        with ServiceLockFile(self.__filePath, timeoutSeconds=self.__timeOutSeconds, retrySeconds=self.__retrySeconds) as lock:  # noqa: F841 pylint: disable=unused-variable
            return self.__deserialize_data()
        return rD

    def __deserialize_data(self, raiseExc=False):
        """Derserialize the history data in the file. Might be locked or not.
        If raiseExc set raise exception on parsing pickle error"""
        rD = {}
        try:
            if not os.access(self.__filePath, os.R_OK):
                logging.warning("No data store in path %r ", self.__filePath)
                return rD
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        try:
            with open(self.__filePath, "rb") as fb:
                while True:
                    # process each record and quit at eof
                    try:
                        d = pickle.load(fb)
                        # logger.info("Read activity record %r" % d)
                        if d["sid"] not in rD:
                            rD[d["sid"]] = {}
                        rD[d["sid"]][d["op"]] = d["data"]
                    except EOFError:
                        break
        except Exception as exc:  # noqa: E722 pylint: disable=bare-except
            if raiseExc:
                logger.error("Deserialization failure with file %s", self.__filePath)
                raise exc
            logger.exception("Deserialization failure with file %s", self.__filePath)

        return rD

    def add(self, sessionId, statusOp, **params):
        """Record a service session tracking record  -

         :param sessionId:  target session identifier
         :param statusOp:   current operation for the tracking record
         :param params:     additional payload of key-values for the tracking record.

        :rtype bool: True for success or False otherwise

        """
        dd = {}
        if params:
            dd = copy.deepcopy(params)
        if self.__useUtc:
            dd["tiso"] = datetime.datetime.utcnow().isoformat()
        else:
            dd["tiso"] = datetime.datetime.now().isoformat()
        tD = {"sid": sessionId, "op": statusOp, "data": dd}
        #
        return self.__serialize(tD, mode="a+b")

    def getHistory(self, lock=True):
        """Return a dictionary image of all session tracking data for the current service user.
        If lock is True, use lockging"""
        if lock:
            return self.__deserialize()
        else:
            # Unlocked - retry on pickle parsing failure
            cnt = 0
            while (cnt < self.__unlocked_maxretry):
                try:
                    rd = self.__deserialize_data(raiseExc=True)
                    return rd
                except pickle.UnpicklingError:
                    cnt += 1
                    logging.error("Could not unpickle unlocked, retry %s", cnt)
                    time.sleep(self.__unlocked_retrySeconds)
            logging.error("Could not parse file.  return empty")
            rD = {}
            return rD

    def getActivitySummary(self):
        """Create a summary of session activity for the service user.

        :rtype dictionary:   dictionary of summary details -
        """
        tD = self.__deserialize()
        #
        rD = {}
        sessionCount = 0
        submittedCount = 0
        completedCount = 0
        failedCount = 0
        sL = []
        #
        try:
            tStart = datetime.datetime(1969, 1, 1).isoformat()  # should always have a "created" in loop
            for sId in tD:
                sD = tD[sId]
                deltaSeconds = 0
                if "created" in sD:
                    sessionCount += 1
                    tStart = sD["created"]["tiso"]
                    st = "created"
                if "submitted" in sD:
                    submittedCount += 1
                    tBegin = sD["submitted"]["tiso"]
                    st = "submitted"
                    #
                    if "failed" in sD:
                        failedCount += 1
                        tEnd = sD["failed"]["tiso"]
                        st = "failed"
                        dt = dateutil.parser.parse(tEnd) - dateutil.parser.parse(tBegin)
                        deltaSeconds = dt.total_seconds()
                    if "completed" in sD:
                        completedCount += 1
                        tEnd = sD["completed"]["tiso"]
                        st = "completed"
                        dt = dateutil.parser.parse(tEnd) - dateutil.parser.parse(tBegin)
                        deltaSeconds = dt.total_seconds()

                    sL.append((sId, tStart, st, deltaSeconds))

            ssL = sorted(sL, key=itemgetter(1))
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("summary construction failing")
        #
        rD["session_count"] = sessionCount
        rD["submitted_count"] = submittedCount
        rD["failed_count"] = failedCount
        rD["completed_count"] = completedCount
        rD["session_list"] = ssL
        return rD
