##
# File: ServiceDataStoreTests.py
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

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import logging
import os
import platform
import sys
import unittest

from wwpdb.utils.ws_utils.ServiceDataStore import ServiceDataStore

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):  # pragma: no cover
    os.makedirs(TESTOUTPUT)

logging.basicConfig(level=logging.DEBUG, format="\n[%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logging.getLogger().setLevel(logging.DEBUG)


class ServiceDataStoreTests(unittest.TestCase):
    def setUp(self):
        self.__sessdir = os.path.join(TESTOUTPUT, "session")
        if not os.path.exists(self.__sessdir):  # pragma: no cover
            os.makedirs(self.__sessdir)

    def testInstantiate(self):
        """Test acquiring new or existing token"""
        tfile = os.path.join(self.__sessdir, "test1-session-store.pic")
        if os.path.exists(tfile):
            os.unlink(tfile)
        sds = ServiceDataStore(self.__sessdir, prefix="test1")
        sds.set("t1", "2")
        self.assertEqual(sds.get("t1"), "2")
        self.assertEqual(sds.get("t2"), "")

        # Try overwrite
        sds.set("t1", "5")
        self.assertEqual(sds.get("t1"), "5")
        sds.set("t1", "2", overWrite=False)
        self.assertEqual(sds.get("t1"), "5")
        sds.set("t1", "2")

        s = sds.dump()
        sys.stderr.write("SDS %s\n" % s)

        # Test update - ensure new values set - but not replace others
        uDict = {"t1": 3, "t2": 2}
        self.assertTrue(sds.update(uDict), "Updating")
        self.assertEqual(sds.get("t1"), "2")  # Did not update
        self.assertEqual(sds.get("t2"), 2)

        # UpdateAll
        uDict = {"t1": 3, "t2": 3, "status": "ok"}
        self.assertTrue(sds.updateAll(uDict), "Update All")
        self.assertEqual(sds.get("t1"), 3)  # Did update now - overwrite
        self.assertEqual(sds.get("t2"), 3)
        self.assertEqual(sds.get("status"), "ok")

        # append
        self.assertTrue(sds.append("t5", 2), "Append")
        self.assertEqual(sds.get("t5"), [2])
        self.assertTrue(sds.append("t5", 3), "Append #2")
        self.assertEqual(sds.get("t5"), [2, 3])

        # extend
        self.assertTrue(sds.extend("t6", [2, 3, 4]), "Extend")
        self.assertEqual(sds.get("t6"), [2, 3, 4])
        self.assertTrue(sds.extend("t6", [2, 3, 4]), "Extend")
        self.assertEqual(sds.get("t6"), [2, 3, 4, 2, 3, 4])

        fp = sds.getFilePath()
        sys.stderr.write("SDS file path %s\n" % fp)
        self.assertNotEqual(fp, "")

        d = sds.getDictionary()
        sys.stderr.write("SDS dictionary %s\n" % d)

        sys.stderr.write("SDS repr %s\n" % sds)


def suiteServiceDataStore():  # pragma: no cover
    suite = unittest.TestSuite()
    suite.addTest(ServiceDataStoreTests("testInstantiate"))
    return suite


if __name__ == "__main__":  # pragma: no cover
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suiteServiceDataStore())
