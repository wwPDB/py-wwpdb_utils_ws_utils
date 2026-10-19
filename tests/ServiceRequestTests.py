##
# File: ServiceRequestTests.py
# Date:  17-Oct-2026
#
# Updates:
##
"""
Test cases for ServiceRequestBase and ServiceRequest classes --

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""

__docformat__ = "restructuredtext en"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import io
import json
import logging
import os
import tempfile
import unittest
from typing import Any, Dict, List

from wwpdb.utils.ws_utils.ServiceRequest import ServiceRequest, ServiceRequestBase

logging.basicConfig(level=logging.DEBUG, format="\n[%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logging.getLogger().setLevel(logging.INFO)


class ServiceRequestBaseTests(unittest.TestCase):
    def testDefaultEmpty(self) -> None:
        req = ServiceRequestBase()
        self.assertEqual(req.getDictionary(), {})
        self.assertFalse(req.exists("a"))
        self.assertEqual(req.getValue("a"), "")
        self.assertIsNone(req.getRawValue("a"))
        self.assertEqual(req.getValueList("a"), [])

    def testValues(self) -> None:
        pD: Dict[str, List[Any]] = {"a": [" val "], "n": [3], "l": [1, 2, 3], "e": [""]}
        req = ServiceRequestBase(pD)
        self.assertTrue(req.exists("a"))
        self.assertEqual(req.getValue("a"), "val")
        self.assertEqual(req.getValue("n"), "3")
        self.assertEqual(req.getRawValue("n"), 3)
        self.assertEqual(req.getValueList("l"), [1, 2, 3])

        self.assertEqual(req.getValueOrDefault("a"), "val")
        self.assertEqual(req.getValueOrDefault("missing", default="dflt"), "dflt")
        # Empty values revert to the default
        self.assertEqual(req.getValueOrDefault("e", default="dflt"), "dflt")

    def testSetters(self) -> None:
        req = ServiceRequestBase()
        self.assertTrue(req.setValue("a", 1))
        self.assertEqual(req.getRawValue("a"), 1)
        self.assertTrue(req.setValueList("l", [4, 5]))
        self.assertEqual(req.getValueList("l"), [4, 5])

        # setDictionary does not overwrite by default
        self.assertTrue(req.setDictionary({"a": 2, "b": 3}))
        self.assertEqual(req.getRawValue("a"), 1)
        self.assertEqual(req.getRawValue("b"), 3)
        self.assertTrue(req.setDictionary({"a": 2}, overWrite=True))
        self.assertEqual(req.getRawValue("a"), 2)

    def testSetterFailures(self) -> None:
        # A container that does not support item assignment
        req = ServiceRequestBase(paramDict=())  # type: ignore[arg-type]
        self.assertFalse(req.setValue("a", 1))
        self.assertFalse(req.setValueList("a", [1]))
        self.assertFalse(req.exists("a"))

    def testExistsFailure(self) -> None:
        # Unhashable key against a dictionary raises internally
        req = ServiceRequestBase({"a": [1]})
        self.assertFalse(req.exists(["a"]))  # type: ignore[arg-type]

    def testJSON(self) -> None:
        pD = {"a": ["1"], "b": ["x", "y"]}
        req = ServiceRequestBase(pD)
        js = req.getJSON()
        self.assertEqual(json.loads(js), pD)

        req2 = ServiceRequestBase()
        req2.setJSON(js)
        self.assertEqual(req2.getDictionary(), pD)

    def testOutput(self) -> None:
        req = ServiceRequestBase({"key1": ["value1"]})
        s = str(req)
        self.assertIn("key1", s)
        self.assertIn("value1", s)
        self.assertEqual(repr(req), s)
        dmp = req.dump()
        self.assertIsNotNone(dmp)
        self.assertIn("key1", str(dmp))

        ofh = io.StringIO()
        req.printIt(ofh)
        self.assertIn("key1", ofh.getvalue())


class ServiceRequestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpdir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.__topPath = self.__tmpdir.name

    def tearDown(self) -> None:
        self.__tmpdir.cleanup()

    def testReturnFormat(self) -> None:
        req = ServiceRequest({})
        # No default set
        self.assertEqual(req.getReturnFormat(), "")

        req = ServiceRequest({})
        req.setDefaultReturnFormat()
        self.assertEqual(req.getReturnFormat(), "html")
        self.assertTrue(req.setReturnFormat())
        self.assertEqual(req.getReturnFormat(), "json")

        # Existing value is not replaced by default
        req = ServiceRequest({"return_format": ["text"]})
        req.setDefaultReturnFormat("json")
        self.assertEqual(req.getReturnFormat(), "text")

    def testRequestPath(self) -> None:
        req = ServiceRequest({"request_path": ["/service/v1/op"]})
        self.assertEqual(req.getRequestPathPrefix(), "")
        self.assertEqual(req.getRequestPath(), "/service/v1/op")

        req.setRequestPathPrefix("/service/v1")
        self.assertEqual(req.getRequestPathPrefix(), "/service/v1")
        self.assertEqual(req.getRequestPath(), "/op")

        req.setRequestPathPrefix("/other")
        self.assertEqual(req.getRequestPath(), "/service/v1/op")

    def testAccessors(self) -> None:
        req = ServiceRequest({"session_id": ["abc"], "semaphore": ["sem1"]})
        self.assertEqual(req.getSessionId(), "abc")
        self.assertEqual(req.getSemaphore(), "sem1")

        self.assertTrue(req.setTopSessionPath(self.__topPath))
        self.assertEqual(req.getTopSessionPath(), self.__topPath)
        self.assertEqual(req.getSessionPath(), os.path.join(self.__topPath, "sessions"))

        self.assertTrue(req.setServiceUserId("user1"))
        self.assertEqual(req.getServiceUserId(), "user1")

        self.assertTrue(req.setSiteId("WWPDB_DEV"))
        self.assertEqual(req.getSiteId(), "WWPDB_DEV")

        self.assertEqual(req.getSessionUserPath(), "")

    def testNewSession(self) -> None:
        req = ServiceRequest({"top_session_path": [self.__topPath], "service_user_id": ["user1"]})
        sObj = req.getSessionObj(new=True)
        sId = sObj.getId()
        assert sId is not None
        self.assertEqual(req.getSessionId(), sId)
        expected = os.path.join(self.__topPath, "sessions", "user1")
        self.assertEqual(req.getSessionUserPath(), expected)
        self.assertTrue(os.path.isdir(os.path.join(expected, sId)))

        # Rejoin existing session
        req2 = ServiceRequest({"top_session_path": [self.__topPath], "service_user_id": ["user1"], "session_id": [sId]})
        sObj2 = req2.getSessionObj()
        self.assertEqual(sObj2.getId(), sId)
        self.assertEqual(sObj2.getPath(), os.path.join(expected, sId))

    def testSessionNoId(self) -> None:
        req = ServiceRequest({"top_session_path": [self.__topPath]})
        sObj = req.getSessionObj()
        self.assertIsNone(sObj.getId())
        self.assertIsNone(sObj.getPath())
        self.assertEqual(req.getSessionUserPath(), os.path.join(self.__topPath, "sessions", "ANONYMOUS"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
