##
# File: ServiceHistoryTests.py
# Date:  26-Dec-201  E. Peisach
#
# Updates:
##
"""
Test cases for ServiceHistoryTests class --

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

from wwpdb.utils.ws_utils.ServiceHistory import ServiceHistory

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):  # pragma: no cover
    os.makedirs(TESTOUTPUT)

logging.basicConfig(level=logging.DEBUG, format="\n[%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logging.getLogger().setLevel(logging.DEBUG)


class ServiceHistoryTests(unittest.TestCase):
    def setUp(self):
        self.__histpath = os.path.join(TESTOUTPUT, "sessionhistory")
        if not os.path.exists(self.__histpath):
            os.makedirs(self.__histpath)  # pragma: no cover

    def testHistory(self):
        """Test acquiring new or existing token"""
        tfile = os.path.join(self.__histpath, "history-session-store.pic")
        if os.path.exists(tfile):
            os.unlink(tfile)

        sh = ServiceHistory(self.__histpath, useUTC=True)
        sessID = "sess1"
        params = {"T1": 1}
        self.assertTrue(sh.add(sessID, "created", **params))
        self.assertTrue(sh.add(sessID, "submitted"))
        # This will be added - but not counted by deserialize
        self.assertTrue(sh.add(sessID, "created"))

        sh2 = ServiceHistory(self.__histpath)
        sessID2 = "sess2"
        self.assertTrue(sh2.add(sessID2, "created"))

        hist = sh.getHistory()
        self.assertEqual(len(hist), 2)
        # sessID/op unique tuples
        self.assertEqual(len(hist[sessID]), 2)
        self.assertEqual(len(hist[sessID2]), 1)

        # Add completion
        self.assertTrue(sh.add(sessID, "completed"))
        self.assertTrue(sh.add(sessID, "failed"))

        # Get summary
        summ = sh.getActivitySummary()
        self.assertEqual(summ["session_count"], 2)
        self.assertEqual(summ["submitted_count"], 1)
        self.assertEqual(summ["failed_count"], 1)
        self.assertEqual(summ["completed_count"], 1)
        print(summ)


def suiteServiceHistory():  # pragma: no cover
    suite = unittest.TestSuite()
    suite.addTest(ServiceHistoryTests("testHistory"))
    return suite


if __name__ == "__main__":  # pragma: no cover
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suiteServiceHistory())
