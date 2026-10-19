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

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import datetime
import logging
import os
import platform
import sys
import unittest
from typing import Optional

from wwpdb.utils.ws_utils.ServiceSmtpUtils import ServiceSmtpUtils
from wwpdb.utils.ws_utils.TokenUtils import JwtTokenReader, JwtTokenUtils

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):  # pragma: no cover
    os.makedirs(TESTOUTPUT)

logging.basicConfig(level=logging.DEBUG, format="\n[%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logging.getLogger().setLevel(logging.INFO)

logger = logging.getLogger()


class MyJwtTokenUtils(JwtTokenUtils):
    def __init__(self, siteId: Optional[str] = None, tokenPrefix: Optional[str] = None) -> None:
        """
        Token utilities for registration webservice

        """
        ssrdPath = os.path.join(TESTOUTPUT, "token_store.pic")
        ssrlPath = os.path.join(TESTOUTPUT)

        super(MyJwtTokenUtils, self).__init__(
            siteId=siteId,
            tokenPrefix=tokenPrefix,
            site_service_registration_dir_path=ssrdPath,
            site_service_registration_lockdir_path=ssrlPath,
        )


class TokenUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tokenPrefix = "VALWS"

    def testGetToken(self) -> None:
        """Test acquiring new or existing token"""
        tU = MyJwtTokenUtils(tokenPrefix=self.__tokenPrefix)
        tokenId, jwtToken = tU.getToken("some.email@noreply.org")
        logger.debug("tokenid %r is %r ", tokenId, jwtToken)
        # Test to ensure proper return
        tD = tU.parseToken(jwtToken)
        tId = tD["sub"]
        logger.debug("token %r payload %r ", tokenId, tD)
        self.assertEqual(tokenId, tId)
        # For coverage
        self.assertIsNotNone(tU.getFilePath())

    def testTokenTimes(self) -> None:
        """Test token access creation and expiration dates"""
        tU = MyJwtTokenUtils(tokenPrefix=self.__tokenPrefix)
        tokenId, jwtToken = tU.getToken("john.westbrook@rcsb.org")
        logger.debug("tokenid %r is %r ", tokenId, jwtToken)
        tD = tU.parseToken(jwtToken)
        if sys.version_info[0] > 2:
            now = datetime.datetime.now(datetime.timezone.utc)
        else:
            now = datetime.datetime.utcnow()  # noqa: DTZ003

        createS = tD["iat"]
        if sys.version_info[0] > 2:
            createT = datetime.datetime.fromtimestamp(createS, datetime.timezone.utc)
        else:
            createT = datetime.datetime.utcfromtimestamp(createS)  # noqa: DTZ004

        difT = now - createT
        logger.debug("token age %f seconds", difT.seconds)

        expS = tD["exp"]
        if sys.version_info[0] > 2:
            expT = datetime.datetime.fromtimestamp(expS, datetime.timezone.utc)
        else:
            expT = datetime.datetime.utcfromtimestamp(expS)  # noqa: DTZ004
        difT = expT - now
        logger.debug("token expires in %f days", difT.days)
        self.assertGreaterEqual(difT.days, 29)

    def testReUseManyTokens(self) -> None:
        """Test the reuse of existing tokens based on an e-mail lookup"""
        tU = MyJwtTokenUtils(tokenPrefix=self.__tokenPrefix)
        for i in range(100):
            tokenId, jwtToken = tU.getToken("john.westbrook@rcsb.org")
            logger.debug("Iteration %3d tokenid %r is %r ", i, tokenId, jwtToken)
            tD = tU.parseToken(jwtToken)
            tId = tD["sub"]
            logger.debug("token %r payload %r ", tokenId, tD)
        self.assertEqual(tokenId, tId)

    def testGetManyTokens(self) -> None:
        """Test generate many new tokens and unique e-mail addresses"""
        tU = MyJwtTokenUtils(tokenPrefix=self.__tokenPrefix)
        for i in range(100):
            tokenId, jwtToken = tU.getToken("john.westbrook%04d@rcsb.org" % i)
            logger.debug("tokenid %r is %r ", tokenId, jwtToken)
            tD = tU.parseToken(jwtToken)
            tId = tD["sub"]
            logger.debug("token %r payload %r ", tokenId, tD)
        self.assertEqual(tokenId, tId)

    def testRemoveTokens(self) -> None:
        """Test remove many tokens by token id"""
        tU = MyJwtTokenUtils(tokenPrefix=self.__tokenPrefix)
        for i in range(100):
            tokenId, jwtToken = tU.getToken("john.westbrook%04d@rcsb.org" % i)
            logger.debug("tokenid %r is %r ", tokenId, jwtToken)
            self.assertTrue(tU.tokenIdExists(tokenId))
            ok = tU.remove(tokenId)
        self.assertEqual(ok, True)

    # Disabled - we do not want email in automated test
    def NoSendToken(self) -> None:  # pragma: no cover
        """Test acquire new or existing token and send token to recipient"""
        tU = MyJwtTokenUtils(tokenPrefix=self.__tokenPrefix)
        tokenId, jwtToken = tU.getToken("john.westbrook@rcsb.org")
        logger.debug("tokenid %r is %r ", tokenId, jwtToken)
        tD = tU.parseToken(jwtToken)
        # tId = tD['sub']
        logger.debug("token %r payload %r ", tokenId, tD)
        msgTemplate = """
This is text is presented on multiple lines.
This is more multi-line text
This is more multi-line text

----------------- Access Token - Remove this surrounding text  ---------------------
%s
-------------------------------- Remove this surrounding text  ---------------------
        """
        msgText = msgTemplate % jwtToken
        tokenFileName = "access-token.jwt"
        with open(tokenFileName, "w") as outfile:
            outfile.write("%s" % jwtToken)
        smtpU = ServiceSmtpUtils()
        ok = smtpU.emailFiles(
            "jwest@rcsb.rutgers.edu",
            "john.westbrook@rcsb.org",
            "TEST SUBJECT",
            msgText,
            fileList=[tokenFileName],
            textAsAttachment=jwtToken,
            textAttachmentName="text-token.jwt",
        )

        self.assertEqual(ok, True)

    def testParseAuth(self) -> None:
        """Test parsing authorization"""
        tU = MyJwtTokenUtils(tokenPrefix=self.__tokenPrefix)
        tokenId, jwtToken = tU.getToken("some.email@noreply.org")

        # Create authorization records - test error casses
        tR = JwtTokenReader()

        aH = "nonbreaer"
        rD = tR.parseAuth(aH)
        self.assertTrue(rD["errorFlag"])

        aH = "bearer"
        rD = tR.parseAuth(aH)
        self.assertTrue(rD["errorFlag"])

        aH = "bearer one two"
        rD = tR.parseAuth(aH)
        self.assertTrue(rD["errorFlag"])

        aH = f"bearer {jwtToken}"
        rD = tR.parseAuth(aH)
        self.assertFalse(rD["errorFlag"])
        self.assertEqual(rD["token"], jwtToken)

        tD = tR.parseToken(jwtToken)
        self.assertFalse(tD["errorCode"])
        self.assertEqual(tD["sub"], tokenId)

    def testTokenReaderParseToken(self) -> None:
        """Test parsing tokens from JwtTokenReader"""

        tR = JwtTokenReader()
        # Validate token
        tD = tR.parseToken("invalidToken")
        self.assertTrue(tD["errorCode"])

        tU = MyJwtTokenUtils(tokenPrefix=self.__tokenPrefix)
        tokenId, jwtToken = tU.getToken("some.email@noreply.org")

        tD = tR.parseToken(jwtToken)
        self.assertFalse(tD["errorCode"])
        self.assertEqual(tD["sub"], tokenId)

        # Create an expired token
        tokenId, jwtToken = tU.getToken("some.email@noreply.org", expireDays=-2)
        tD = tR.parseToken(jwtToken)
        self.assertTrue(tD["errorCode"])
        self.assertEqual(tD["errorMessage"], "API access token has expired")

    def testTokenUtilsParseToken(self) -> None:
        """Test parsing tokens from TokenUtils"""

        tU = MyJwtTokenUtils(tokenPrefix=self.__tokenPrefix)

        tD = tU.parseToken("invalidToken")
        self.assertTrue(tD["errorCode"])

        tokenId, jwtToken = tU.getToken("some.email@noreply.org")

        tD = tU.parseToken(jwtToken)
        self.assertFalse(tD["errorCode"])
        self.assertEqual(tD["sub"], tokenId)

        # Create an expired token
        tokenId, jwtToken = tU.getToken("some.email@noreply.org", expireDays=-2)
        tD = tU.parseToken(jwtToken)
        self.assertTrue(tD["errorCode"])
        self.assertEqual(tD["errorMessage"], "API access token has expired")

    def testTokenUtilsParseAuth(self) -> None:
        """Test parsing authorization"""
        tU = MyJwtTokenUtils(tokenPrefix=self.__tokenPrefix)
        _tokenId, jwtToken = tU.getToken("some.email@noreply.org")  # pylint: disable=unused-variable

        aH = "nonbreaer"
        rD = tU.parseAuth(aH)
        self.assertTrue(rD["errorFlag"])

        aH = "bearer"
        rD = tU.parseAuth(aH)
        self.assertTrue(rD["errorFlag"])

        aH = "bearer one two"
        rD = tU.parseAuth(aH)
        self.assertTrue(rD["errorFlag"])

        aH = f"bearer {jwtToken}"
        rD = tU.parseAuth(aH)
        self.assertFalse(rD["errorFlag"])
        self.assertEqual(rD["token"], jwtToken)


def suiteTokenGen() -> unittest.TestSuite:  # pragma: no cover
    suite = unittest.TestSuite()
    suite.addTest(TokenUtilsTests("testGetToken"))
    suite.addTest(TokenUtilsTests("testTokenTimes"))
    suite.addTest(TokenUtilsTests("testReUseManyTokens"))
    suite.addTest(TokenUtilsTests("testGetManyTokens"))
    suite.addTest(TokenUtilsTests("testRemoveTokens"))
    suite.addTest(TokenUtilsTests("testTokenUtilsParseToken"))
    suite.addTest(TokenUtilsTests("testTokenUtilsParseAuth"))
    return suite


def suiteTokenSend() -> unittest.TestSuite:  # pragma: no cover
    suite = unittest.TestSuite()
    suite.addTest(TokenUtilsTests("testSendToken"))
    return suite


def suiteTokenReader() -> unittest.TestSuite:  # pragma: no cover
    suite = unittest.TestSuite()
    suite.addTest(TokenUtilsTests("testParseAuth"))
    suite.addTest(TokenUtilsTests("testTokenReaderParseToken"))
    return suite


if __name__ == "__main__":  # pragma: no cover
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suiteTokenGen())
    # runner.run(suiteTokenSend())
    runner.run(suiteTokenReader())
