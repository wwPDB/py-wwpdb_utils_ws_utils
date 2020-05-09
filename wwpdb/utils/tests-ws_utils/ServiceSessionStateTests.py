##
# File: ServiceSessionStateTests.py
# Date:  26-Dec-201  E. Peisach
#
# Updates:
##
"""
Test cases for ServiceDataStoreTests class --

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
from __future__ import division, absolute_import, print_function

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import unittest
import os
import platform
import logging

from wwpdb.utils.ws_utils.ServiceSessionState import ServiceSessionState

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):  # pragma: no cover
    os.makedirs(TESTOUTPUT)

logging.basicConfig(level=logging.DEBUG, format="\n[%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logging.getLogger().setLevel(logging.DEBUG)


class ServiceSessionStateTests(unittest.TestCase):
    def testInstantiate(self):
        """Test ServiceSessionState functionality"""
        sst = ServiceSessionState()
        paramdict = {"test": ["1"], "second": ["2"]}
        ok = sst.setAppDataDict(paramdict)
        self.assertTrue(ok)

        # This should fail as expect dictionary
        ok = sst.setAppDataDict([1, 2, 3])
        self.assertFalse(ok)

        # Set value
        ok = sst.setAppData("third", ["3"])
        self.assertTrue(ok)

        # Will fail - key cannot be mutable - and a list is
        ok = sst.setAppData([1, 2, 3], ["3"])
        self.assertFalse(ok)

        # Check dictionary contents
        rd = sst.getAppDataDict()
        self.assertEqual(len(rd), 3)
        self.assertEqual(rd["third"], ["3"])

        # Default json
        self.assertEqual(sst.getResponseFormat(), "json")

        # Upload/Download
        self.assertEqual(sst.getDownloadList(), [])
        self.assertTrue(sst.setDownload("art.txt", "/tmp/art.txt"))
        self.assertTrue(sst.setDownload("bar.txt", "/tmp/art.txt", contentType="secretcontent", md5Digest="12a"))
        self.assertEqual(len(sst.getDownloadList()), 2)

        self.assertEqual(sst.getUploadList(), [])
        self.assertTrue(sst.setUpload("art.txt", "/tmp/art.txt"))
        self.assertTrue(sst.setUpload("bar.txt", "/tmp/art.txt", contentType="secretcontent", md5Digest="12a"))
        self.assertEqual(len(sst.getUploadList()), 2)

        self.assertEqual(sst.getResponseFormat(), "files")

        # assign
        ok = sst.assign("superservice", {"A": 1, "B": 2}, True)
        self.assertTrue(ok)

        sst.setResponseFormat("html")
        self.assertEqual(sst.getResponseFormat(), "html")

        sst.setServiceName("Magic")
        self.assertEqual(sst.getServiceName(), "Magic")

        sst.setServiceArgs([1, 2, 3])
        self.assertEqual(sst.getServiceArgs(), [1, 2, 3])

        sst.setServiceStatusText("good")
        self.assertEqual(sst.getServiceStatusText(), "good")

        sst.setServiceCompletionFlag(True)
        self.assertFalse(sst.getServiceErrorFlag())
        sst.setServiceCompletionFlag(False)
        self.assertTrue(sst.getServiceErrorFlag())

        sst.setServiceError("Failed because")
        self.assertTrue(sst.getServiceErrorFlag())
        sst.setServiceError("Failed because warn", errFlag=False)
        self.assertFalse(sst.getServiceErrorFlag())
        self.assertEqual(sst.getServiceErrorMessage(), "Failed because warn")

        sst.setServiceWarning("Warn because")
        self.assertTrue(sst.getServiceWarningFlag())
        sst.setServiceWarning("Failed because no warn", warnFlag=False)
        self.assertFalse(sst.getServiceWarningFlag())
        self.assertEqual(sst.getServiceWarningMessage(), "Failed because no warn")

        sst.setServiceErrorMessage("Test")
        self.assertEqual(sst.getServiceErrorMessage(), "Test")

        sst.setServiceWarningMessage("Test2")
        self.assertEqual(sst.getServiceWarningMessage(), "Test2")


def suiteSessionStateTests():  # pragma: no cover
    suite = unittest.TestSuite()
    suite.addTest(ServiceSessionStateTests("testInstantiate"))
    return suite


if __name__ == "__main__":  # pragma: no cover
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suiteSessionStateTests())
