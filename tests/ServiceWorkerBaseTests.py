##
# File: ServiceWorkerBaseTests.py
# Date:  17-Oct-2026
#
# Updates:
##
"""
Test cases for ServiceWorkerBase class.  ConfigInfo is mocked.

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""

__docformat__ = "restructuredtext en"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import logging
import tempfile
import unittest
from typing import Any, Dict, Optional
from unittest import mock

from wwpdb.utils.ws_utils.ServiceRequest import ServiceRequest
from wwpdb.utils.ws_utils.ServiceSessionState import ServiceSessionState
from wwpdb.utils.ws_utils.ServiceWorkerBase import ServiceWorkerBase

logging.basicConfig(level=logging.DEBUG, format="\n[%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logging.getLogger().setLevel(logging.INFO)


class MyServiceWorker(ServiceWorkerBase):
    """Concrete worker exposing the protected base class API for testing"""

    def __init__(self, reqObj: ServiceRequest, sessionDataPrefix: Optional[str] = None) -> None:
        super().__init__(reqObj=reqObj, sessionDataPrefix=sessionDataPrefix)
        self.addService("/service/op1", "op1")
        self.addServices({"/service/op2": "op2", "/service/bad": "missingOp"})

    def op1(self) -> ServiceSessionState:
        sst = ServiceSessionState()
        sst.setServiceStatusText("op1 done")
        return sst

    def op2(self) -> ServiceSessionState:
        raise ValueError("op2 failure")

    def run(self, reqPath: Optional[str] = None) -> ServiceSessionState:
        return self._run(reqPath)

    def getSession(
        self, new: bool = False, useContext: bool = False, contextOverWrite: bool = True, trackHistory: bool = True
    ) -> bool:
        return self._getSession(
            new=new, useContext=useContext, contextOverWrite=contextOverWrite, trackHistory=trackHistory
        )

    def appendSessionStore(self, iD: Any = None) -> bool:
        return self._appendSessionStore(iD)

    def getSessionStoreDict(self) -> Dict[str, Any]:
        return self._getSessionStoreDict()

    def setSessionStoreValue(self, ky: str, val: Any) -> Any:
        return self._setSessionStoreValue(ky, val)

    def trackServiceStatus(self, op: str, **params: Any) -> bool:
        return self._trackServiceStatus(op, **params)

    def getServiceActivitySummary(self) -> Dict[str, Any]:
        return self._getServiceActivitySummary()


class ServiceWorkerBaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpdir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.__topPath = self.__tmpdir.name
        patcher = mock.patch("wwpdb.utils.ws_utils.ServiceWorkerBase.ConfigInfo")
        self.__mConfigInfo = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self) -> None:
        self.__tmpdir.cleanup()

    def __makeRequest(self, **kw: Any) -> ServiceRequest:
        pD: Dict[str, Any] = {
            "top_session_path": [self.__topPath],
            "service_user_id": ["user1"],
            "wwpdb_site_id": ["WWPDB_TEST"],
            "request_path": ["/service/op1"],
            "remote_addr": ["127.0.0.1"],
        }
        for k, v in kw.items():
            pD[k] = [v]
        return ServiceRequest(pD)

    def testInit(self) -> None:
        MyServiceWorker(self.__makeRequest())
        self.__mConfigInfo.assert_called_once_with("WWPDB_TEST")

    def testRun(self) -> None:
        sw = MyServiceWorker(self.__makeRequest())
        # Path from request
        sst = sw.run()
        self.assertFalse(sst.getServiceErrorFlag())
        self.assertEqual(sst.getServiceStatusText(), "op1 done")

        sst = sw.run("/service/unknown")
        self.assertTrue(sst.getServiceErrorFlag())
        self.assertEqual(sst.getServiceErrorMessage(), "Unknown operation")

        # Operation raises
        sst = sw.run("/service/op2")
        self.assertTrue(sst.getServiceErrorFlag())
        self.assertEqual(sst.getServiceErrorMessage(), "Operation failure")

        # Operation registered but no such method
        sst = sw.run("/service/bad")
        self.assertTrue(sst.getServiceErrorFlag())
        self.assertEqual(sst.getServiceErrorMessage(), "Operation failure")

    def testSessionStoreWithoutSession(self) -> None:
        sw = MyServiceWorker(self.__makeRequest())
        # No session store yet - failures are caught
        self.assertTrue(sw.appendSessionStore(None))
        self.assertFalse(sw.appendSessionStore({"a": 1}))
        self.assertEqual(sw.getSessionStoreDict(), {})
        self.assertEqual(sw.setSessionStoreValue("a", 1), {})

    def testNewSession(self) -> None:
        req = self.__makeRequest()
        sw = MyServiceWorker(req, sessionDataPrefix="testprefix")
        self.assertTrue(sw.getSession(new=True))
        self.assertNotEqual(req.getSessionId(), "")

        sD = sw.getSessionStoreDict()
        self.assertIn("session_history", sD)
        self.assertEqual(len(sD["session_history"]), 1)
        rP, _tS, msg = sD["session_history"][0]
        self.assertEqual(rP, "/service/op1")
        self.assertEqual(msg, "begins")

        self.assertTrue(sw.appendSessionStore({"k1": "v1"}))
        self.assertTrue(sw.setSessionStoreValue("k2", "v2"))
        sD = sw.getSessionStoreDict()
        self.assertEqual(sD["k1"], "v1")
        self.assertEqual(sD["k2"], "v2")

    def testJoinSessionWithContext(self) -> None:
        req = self.__makeRequest()
        sw = MyServiceWorker(req)
        self.assertTrue(sw.getSession(new=True, trackHistory=False))
        self.assertNotIn("session_history", sw.getSessionStoreDict())
        sw.setSessionStoreValue("stored_key", "stored_value")
        sw.setSessionStoreValue("remote_addr", "10.0.0.1")
        sessionId = req.getSessionId()

        # Rejoin without overwriting existing request values
        req2 = self.__makeRequest(session_id=sessionId)
        sw2 = MyServiceWorker(req2)
        self.assertTrue(sw2.getSession(useContext=True, contextOverWrite=False))
        self.assertEqual(req2.getValue("stored_key"), "stored_value")
        self.assertEqual(req2.getValue("remote_addr"), "127.0.0.1")

        # Rejoin overwriting request values
        req3 = self.__makeRequest(session_id=sessionId)
        sw3 = MyServiceWorker(req3)
        self.assertTrue(sw3.getSession(useContext=True))
        self.assertEqual(req3.getValue("remote_addr"), "10.0.0.1")

    def testJoinMissingSession(self) -> None:
        req = self.__makeRequest(session_id="doesnotexist")
        sw = MyServiceWorker(req)
        self.assertFalse(sw.getSession())

    def testGetSessionFailure(self) -> None:
        req = self.__makeRequest()
        sw = MyServiceWorker(req)
        with mock.patch.object(req, "getSessionObj", side_effect=RuntimeError("boom")):
            self.assertFalse(sw.getSession(new=True))

    def testTrackServiceStatus(self) -> None:
        req = self.__makeRequest()
        sw = MyServiceWorker(req)
        self.assertTrue(sw.getSession(new=True))
        self.assertTrue(sw.trackServiceStatus("created"))
        self.assertTrue(sw.trackServiceStatus("completed", detail="all good"))
        # Explicit remote_addr is retained
        self.assertTrue(sw.trackServiceStatus("failed", remote_addr="10.0.0.2"))

        summary = sw.getServiceActivitySummary()
        self.assertIsInstance(summary, dict)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
