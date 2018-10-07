##
# File: TokenUtilsTests.py
# Date:  12-July-2016  J. Westbrook
#
# Updates:
##
"""
Test cases for TokenUtils class --

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
from __future__ import division, absolute_import, print_function

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import unittest
import os
import platform
import sys
import datetime
import logging
import pytz
from past.builtins import xrange

from wwpdb.utils.ws_utils.TokenUtils import JwtTokenUtils
from wwpdb.utils.ws_utils.ServiceSmtpUtils import ServiceSmtpUtils

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, 'test-output', platform.python_version())
if not os.path.exists(TESTOUTPUT):
    os.makedirs(TESTOUTPUT)

logging.basicConfig(level=logging.DEBUG, format='\n[%(levelname)s]-%(module)s.%(funcName)s: %(message)s')
logging.getLogger().setLevel(logging.DEBUG)

class MyJwtTokenUtils(JwtTokenUtils):
    def __init__(self, siteId=None, tokenPrefix=None):
        """
        Token utilities for registration webservice

        """
        ssrdPath = os.path.join(TESTOUTPUT, "token_store.pic")
        ssrlPath = os.path.join(TESTOUTPUT)

        super(MyJwtTokenUtils, self).__init__(siteId=siteId, tokenPrefix=tokenPrefix,
                                              site_service_registration_dir_path = ssrdPath,
                                              site_service_registration_lockdir_path = ssrlPath)
            

class TokenUtilsTests(unittest.TestCase):

    def setUp(self):
        self.__tokenPrefix="VALWS"
        pass

    def testGetToken(self):
        ''' Test acquiring new or existing token'''
        tU = MyJwtTokenUtils(tokenPrefix=self.__tokenPrefix)
        tokenId, jwtToken = tU.getToken('john.westbrook@rcsb.org')
        logging.debug("tokenid %r is %r " % (tokenId, jwtToken))
        tD = tU.parseToken(jwtToken)
        tId = tD['sub']
        logging.debug("token %r payload %r " % (tokenId, tD))
        self.assertEqual(tokenId, tId)

    def testTokenTimes(self):
        ''' Test token access creation and expiration dates'''
        tU = MyJwtTokenUtils(tokenPrefix=self.__tokenPrefix)
        tokenId, jwtToken = tU.getToken('john.westbrook@rcsb.org')
        logging.debug("tokenid %r is %r " % (tokenId, jwtToken))
        tD = tU.parseToken(jwtToken)
        now = datetime.datetime.utcnow()

        createS = tD['iat']
        createT = datetime.datetime.utcfromtimestamp(createS)
        difT = now - createT
        logging.debug("token age %f seconds" % difT.seconds)

        expS = tD['exp']
        expT = datetime.datetime.utcfromtimestamp(expS)
        difT = expT - now
        logging.debug("token expires in %f days" % difT.days)
        self.assertGreaterEqual(difT.days, 29)

    def testReUseManyTokens(self):
        '''Test the reuse of existing tokens based on an e-mail lookup'''
        tU = MyJwtTokenUtils(tokenPrefix=self.__tokenPrefix)
        for i in xrange(0, 100):
            tokenId, jwtToken = tU.getToken('john.westbrook@rcsb.org')
            logging.debug("Iteration %3d tokenid %r is %r " % (i, tokenId, jwtToken))
            tD = tU.parseToken(jwtToken)
            tId = tD['sub']
            logging.debug("token %r payload %r " % (tokenId, tD))
        self.assertEqual(tokenId, tId)

    def testGetManyTokens(self):
        '''Test generate many new tokens and unique e-mail addresses'''
        tU = MyJwtTokenUtils(tokenPrefix=self.__tokenPrefix)
        for i in xrange(0, 100):
            tokenId, jwtToken = tU.getToken('john.westbrook%04d@rcsb.org' % i)
            logging.debug("tokenid %r is %r " % (tokenId, jwtToken))
            tD = tU.parseToken(jwtToken)
            tId = tD['sub']
            logging.debug("token %r payload %r " % (tokenId, tD))
        self.assertEqual(tokenId, tId)

    def testRemoveTokens(self):
        '''Test remove many tokens by token id '''
        tU = MyJwtTokenUtils(tokenPrefix=self.__tokenPrefix)
        for i in xrange(0, 100):
            tokenId, jwtToken = tU.getToken('john.westbrook%04d@rcsb.org' % i)
            logging.debug("tokenid %r is %r " % (tokenId, jwtToken))
            ok = tU.remove(tokenId)
        self.assertEqual(ok, True)

    # Disabled - we do not want email in automated test
    def NoSendToken(self):
        '''Test acquire new or existing token and send token to recipient '''
        tU = MyJwtTokenUtils(tokenPrefix=self.__tokenPrefix)
        tokenId, jwtToken = tU.getToken('john.westbrook@rcsb.org')
        logging.debug("tokenid %r is %r " % (tokenId, jwtToken))
        tD = tU.parseToken(jwtToken)
        tId = tD['sub']
        logging.debug("token %r payload %r " % (tokenId, tD))
        #
        msgText = '''
This is text is presented on multiple lines.
This is more multi-line text
This is more multi-line text

----------------- Access Token - Remove this surrounding text  ---------------------
%s
-------------------------------- Remove this surrounding text  ---------------------
        ''' % jwtToken
        #
        tokenFileName = "access-token.jwt"
        with open(tokenFileName, 'wb') as outfile:
            outfile.write("%s" % jwtToken)
        smtpU = ServiceSmtpUtils()
        ok = smtpU.emailFiles('jwest@rcsb.rutgers.edu', 'john.westbrook@rcsb.org', 'TEST SUBJECT', msgText,
                           fileList=[tokenFileName], textAsAttachment=jwtToken, textAttachmentName="text-token.jwt")

        self.assertEqual(ok, True)


def suiteTokenGen():
    suite = unittest.TestSuite()
    suite.addTest(TokenUtilsTests('testGetToken'))
    suite.addTest(TokenUtilsTests('testTokenTimes'))
    suite.addTest(TokenUtilsTests('testReUseManyTokens'))
    suite.addTest(TokenUtilsTests('testGetManyTokens'))
    suite.addTest(TokenUtilsTests('testRemoveTokens'))
    return suite


def suiteTokenSend():
    suite = unittest.TestSuite()
    suite.addTest(TokenUtilsTests('testSendToken'))
    #
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suiteTokenGen())
    runner.run(suiteTokenSend())
