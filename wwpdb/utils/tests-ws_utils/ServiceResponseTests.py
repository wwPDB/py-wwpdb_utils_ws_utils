##
# File: ServiceResponseTests.py
# Date:  26-Dec-2019  E. Peisach
#
# Updates:
##
"""
Test cases for ServiceResponseTests class --

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
import sys
import os
import platform
import logging

from wwpdb.utils.ws_utils.ServiceResponse import ServiceResponse

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):  # pragma: no cover
    os.makedirs(TESTOUTPUT)

logging.basicConfig(level=logging.DEBUG, format="\n[%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logging.getLogger().setLevel(logging.DEBUG)


class ServiceResponseTests(unittest.TestCase):
    def setUp(self):
        self.__sr = ServiceResponse()

    def testSetError(self):
        """ Test setting error"""
        self.assertFalse(self.__sr.isError())
        self.__sr.setError(statusCode=200, msg="Some error")
        self.assertTrue(self.__sr.isError())

    def testSetData(self):
        """ Test setting data"""
        self.assertEqual(self.__sr.getData(), {})
        dt = {"1": 2}
        self.__sr.setData(dt)
        self.assertEqual(self.__sr.getData(), dt)

    def testHtml(self):
        """ Test html list actions"""
        self.__sr.setHtmlList()
        self.__sr.setHtmlList(["Test file is foo.py", "Of two items"])
        self.__sr.appendHtmlList(["Some other data", "with two items"])
        sys.stderr.write("%s\n" % self.__sr.dump())
        self.__sr.setHtmlText("Setting direct")
        self.__sr.setReturnFormat("html")
        resp = self.__sr.getResponse()  # noqa: F841 pylint: disable=unused-variable

        # Templates
        self.__sr.setHtmlTextFromTemplate(os.path.join(HERE, "template.txt"), HERE, parameterDict={"T1": 2})
        sys.stderr.write("%s\n" % self.__sr.dump())

    def testSet(self):
        """Random tests of setting values"""
        # Link content
        self.__sr.setHtmlLinkText("htmltext")
        self.__sr.setText("Randomtext")

        sys.stderr.write("testSet output %s\n" % self.__sr.dump())
        self.__sr.setTextFile(os.path.join(HERE, "template.txt"))
        self.__sr.setHtmlContentPath("https://wwpdb.org")
        self.assertEqual(("text/plain", None), self.__sr.getMimetypeAndEncoding(os.path.join(HERE, "template.txt")))

        self.__sr.setReturnFormat("html")
        resp = self.__sr.getResponse()  # noqa: F841 pylint: disable=unused-variable

        self.assertTrue(self.__sr.setBinaryFile(os.path.join(HERE, "template.txt")))


def suiteServiceResponse():  # pragma: no cover
    suite = unittest.TestSuite()
    suite.addTest(ServiceResponseTests("testSetError"))
    suite.addTest(ServiceResponseTests("testSetData"))
    suite.addTest(ServiceResponseTests("testHtml"))
    suite.addTest(ServiceResponseTests("testSet"))
    return suite


if __name__ == "__main__":  # pragma: no cover
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suiteServiceResponse())
