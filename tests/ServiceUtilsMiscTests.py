##
# File: ServiceUtilsMiscTests.py
# Date:  26-Dec-201  E. Peisach
#
# Updates:
##
"""
Test cases for ServiceUtilsMiscTests class --

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

from wwpdb.utils.ws_utils.ServiceUtilsMisc import getMD5

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):  # pragma: no cover
    os.makedirs(TESTOUTPUT)

logging.basicConfig(level=logging.DEBUG, format="\n[%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logging.getLogger().setLevel(logging.DEBUG)


class ServiceUtilsMiscTests(unittest.TestCase):
    def setUp(self):
        pass

    def testMD5(self):
        """Test MD5 calculation"""
        md5 = getMD5(__file__, block_size=50)
        sys.stderr.write("MD5 size=50:  %s\n" % md5)
        md5_2 = getMD5(__file__)
        sys.stderr.write("MD5 size=def:  %s\n" % md5_2)
        self.assertEqual(md5, md5_2)

        md5 = getMD5(__file__, block_size=50, hr=False)
        sys.stderr.write("MD5 size=50, nohr:  %s\n" % md5)


def suiteServiceUtilsMisc():  # pragma: no cover
    suite = unittest.TestSuite()
    suite.addTest(ServiceUtilsMiscTests("testMD5"))
    return suite


if __name__ == "__main__":  # pragma: no cover
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suiteServiceUtilsMisc())
