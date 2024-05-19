##
# File:  TokenUtils.py
# Date:  10-July-2016
#
# Updates:
#   2-Aug-2016 jdw standardized error diagnostics --
#  25-Sep-2016 jdw revise exception messages
#  13-Feb-2017 jdw add token prefix to foken data store file name -
##
"""
Base class for supporting application token management.

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

import os
import datetime

try:
    import cPickle as pickle
except ImportError:
    import pickle

import jwt
from oslo_concurrency import lockutils

import logging

#
from wwpdb.utils.config.ConfigInfo import ConfigInfo

logger = logging.getLogger()


class TokenUtilsBase(object):
    def __init__(self, siteId=None, tokenPrefix=None, **kwargs):
        """
        Base class supporting application token management in persistent store.
        kwargs allows for overriding ConfigInfo for testing

        """
        #
        self._cI = ConfigInfo(siteId)
        #
        if tokenPrefix is not None:
            fn = tokenPrefix + "_TOKEN_STORE.pic"
        else:
            fn = "ANONYMOUSWS_TOKEN_STORE.pic"
        #
        self.__filePath = kwargs.get("site_service_registration_dir_path")
        if not self.__filePath:
            self.__filePath = os.path.join(self._cI.get("SITE_SERVICE_REGISTRATION_DIR_PATH"), fn)
        #
        logger.debug("Assigning token store file path %r", self.__filePath)
        self.__lockDirPath = kwargs.get("site_service_registration_lockdir_path")
        if not self.__lockDirPath:
            self.__lockDirPath = self._cI.get("SITE_SERVICE_REGISTRATION_LOCKDIR_PATH", ".")
        #
        self.__tokenD = {}
        self.__emailD = {}
        self.__tokenPrefix = tokenPrefix if tokenPrefix else "WS"
        self.__pickleProtocol = 0
        #
        lockutils.set_defaults(self.__lockDirPath)
        #
        self.deserialize()

    def __makeTokenId(self, iVal):
        return "%s_%010d" % (self.__tokenPrefix, iVal)

    def __parseTokenId(self, tokenId):
        try:
            pL = tokenId.split("_")
            prefix = pL[0]
            iVal = int(pL[1])
            return (prefix, iVal)
        except:  # noqa: E722 pylint: disable=bare-except
            return (None, None)

    def getFilePath(self):
        return self.__filePath

    @lockutils.synchronized("tokenutils.serialize-lock", external=True)
    def serialize(self):
        try:
            with open(self.__filePath, "wb") as outfile:
                pickle.dump(self.__tokenD, outfile, self.__pickleProtocol)
                pickle.dump(self.__emailD, outfile, self.__pickleProtocol)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILING")
        return False

    def deserialize(self):
        try:
            with open(self.__filePath, "rb") as outfile:
                self.__tokenD = pickle.load(outfile)
                self.__emailD = pickle.load(outfile)
            logger.debug("Recovered %4d token Ids %4d e-mails", len(self.__tokenD), len(self.__emailD))
            return True
        except Exception as e:
            logger.debug("Unable to deserialize persistent token store %r - %r", self.__filePath, str(e))
        return False

    def tokenIdExists(self, tokenId):
        try:
            return tokenId in self.__tokenD
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return False

    def tokenIdEmailExists(self, email):
        try:
            return email in self.__emailD
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return False

    @lockutils.synchronized("tokenutils.transaction-lock", external=True)
    def remove(self, tokenId):
        self.serialize()
        try:
            email = self.getTokenIdEmail(tokenId)
            if email in self.__emailD:
                del self.__emailD[email]
        except:  # noqa: E722 pylint: disable=bare-except
            self.deserialize()
            return False
        try:
            del self.__tokenD[tokenId]
        except:  # noqa: E722 pylint: disable=bare-except
            self.deserialize()
            return False
        self.serialize()
        return True

    def getTokenIdEmail(self, tokenId):
        try:
            return self.__tokenD[tokenId]["email"]
        except:  # noqa: E722 pylint: disable=bare-except
            return ""

    def saveTokenId(self, tokenId, email, **kw):
        """"""
        if tokenId is None or len(tokenId) < 12 or email is None or len(email) < 3:
            return False
        try:

            tD = {"email": email}
            tD.update(kw)
            self.__tokenD[tokenId] = tD
            self.__emailD[email] = tokenId
            self.serialize()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Token save FAILING")
        return False

    def fetchTokenId(self, email):
        """Return any existing token assigned to the input e-mail or create the next token
        identifer with this e-mail assignment.
        """
        try:
            return self.__emailD[email]
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        #
        #  Create a new tokenId and save -
        #
        iVal = self.__nextTokenId()
        tokenId = self.__makeTokenId(iVal)
        self.saveTokenId(tokenId, email)

        return tokenId

    def __nextTokenId(self):
        """Return the next token identifier string (e.g. N+1 for <PREFIX>_0000000N)

        return 1-N for success or -1 for failure
        """
        try:
            if len(self.__tokenD.keys()) > 0:
                tokenMax = max(self.__tokenD.keys())
                _pr, iV = self.__parseTokenId(tokenMax)
                iV += 1
            else:
                iV = 1
            return iV
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILING")

        return -1


class JwtTokenUtils(TokenUtilsBase):
    def __init__(self, siteId=None, tokenPrefix=None, **kwargs):
        """
        Token utilities for registration webservice

        """
        super(JwtTokenUtils, self).__init__(siteId=siteId, tokenPrefix=tokenPrefix, **kwargs)
        #
        # self.__inputToken = self._reqObj.getValue('authorization').split()[1]
        #
        serviceKey = self._cI.get("SITE_SERVICE_REGISTRATION_KEY", None)
        self.__serviceKey = serviceKey if serviceKey else "secretvalue"
        self.__tokenErrorCode = 401

    def parseAuth(self, authHeader):
        rD = {"errorCode": None, "errorMessage": None, "token": None, "errorFlag": False}
        parts = authHeader.split()
        if parts[0].lower() != "bearer":
            rD = {"errorCode": self.__tokenErrorCode, "errorMessage": "Authorization header must start with Bearer", "errorFlag": True}
        elif len(parts) == 1:
            rD = {"errorCode": self.__tokenErrorCode, "errorMessage": "API access token not found", "errorFlag": True}
        elif len(parts) > 2:
            rD = {"errorCode": self.__tokenErrorCode, "errorMesage": "Authorization header must be Bearer token", "errorFlag": True}
        if not rD["errorFlag"]:
            rD["token"] = parts[1]
        return rD

    def parseToken(self, token):
        """Return data payload for the input token along with any error diagnostics -"""
        return self.__getTokenData(token)

    def getToken(self, email, expireDays=30):
        """Return a tokenId and a jwt token for the input e-mail address.
        Existing tokenId's are reused with the existing email address.

        """
        tokenId = self.fetchTokenId(email)
        jwtToken = self.__create_token(tokenId, self.__serviceKey, expireDays=expireDays)
        return tokenId, jwtToken

    def __create_token(self, tokenId, secretKey, expireDays=30, algorithm="HS256", encoding="utf-8"):
        payload = {
            #        using the standard JWT claim keys --
            # subject id
            "sub": tokenId,
            # creation datetime
            "iat": datetime.datetime.utcnow(),
            # expiration datetime
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=expireDays),
        }
        token = jwt.encode(payload, secretKey, algorithm=algorithm)
        #
        # PyJwt 2.x return string
        #
        if int(jwt.__version__.split(".")[0]) >= 2:
            return token
        else:
            #
            # 'utf-8' or 'unicode_escape'?
            #
            return token.decode(encoding)

    def __parseToken(self, token, secretKey="secretvalue", algorithm="HS256"):
        return jwt.decode(token, secretKey, algorithms=algorithm)

    def __getTokenData(self, token):
        """Return token payload as a dictionary and processing diagnostics -"""
        errorCode = None
        errorMessage = None
        tokenData = {}
        #
        if token is None:
            errorMessage = "Missing token"
        try:
            tokenData = self.__parseToken(token, secretKey=self.__serviceKey)
        except jwt.DecodeError:
            errorMessage = "API access token is invalid"
            errorCode = self.__tokenErrorCode
        except jwt.ExpiredSignatureError:
            errorMessage = "API access token has expired"
            errorCode = self.__tokenErrorCode
        except:  # noqa: E722 pylint: disable=bare-except
            errorMessage = "API access token processing error"
            errorCode = self.__tokenErrorCode

        tokenData["errorCode"] = errorCode
        tokenData["errorMessage"] = errorMessage
        tokenData["errorFlag"] = errorMessage is not None

        return tokenData


class JwtTokenReader(object):
    def __init__(self, siteId=None):
        """
        Limited set of token methods required to read and validate a JWT tokens.

        """
        self._cI = ConfigInfo(siteId)
        serviceKey = self._cI.get("SITE_SERVICE_REGISTRATION_KEY", default=None)
        self.__serviceKey = serviceKey if serviceKey else "secretvalue"
        self.__tokenErrorCode = 401

    def parseAuth(self, authHeader):
        rD = {"errorCode": None, "errorMessage": None, "token": None, "errorFlag": False}
        parts = authHeader.split()
        if parts[0].lower() != "bearer":
            rD = {"errorCode": self.__tokenErrorCode, "errorMessage": "Authorization header must start with Bearer", "errorFlag": True}
        elif len(parts) == 1:
            rD = {"errorCode": self.__tokenErrorCode, "errorMessage": "API access token not found", "errorFlag": True}
        elif len(parts) > 2:
            rD = {"errorCode": self.__tokenErrorCode, "errorMesage": "Authorization header must be Bearer token", "errorFlag": True}
        if not rD["errorFlag"]:
            rD["token"] = parts[1]
        return rD

    def parseToken(self, token):
        """Return data payload for the input token along with any error diagnostics -"""
        return self.__getTokenData(token)

    def __parseToken(self, token, secretKey="secretvalue", algorithm="HS256"):
        return jwt.decode(token, secretKey, algorithms=algorithm)

    def __getTokenData(self, token):
        """Return token payload as a dictionary and processing diagnostics -"""
        errorCode = None
        errorMessage = None
        tokenData = {}
        #
        if token is None:
            errorMessage = "Missing token"
        try:
            tokenData = self.__parseToken(token, secretKey=self.__serviceKey)
        except jwt.DecodeError:
            errorMessage = "API access token is invalid"
            errorCode = self.__tokenErrorCode
        except jwt.ExpiredSignatureError:
            errorMessage = "API access token has expired"
            errorCode = self.__tokenErrorCode
        except:  # noqa: E722 pylint: disable=bare-except
            errorMessage = "API access token processing error"
            errorCode = self.__tokenErrorCode

        tokenData["errorCode"] = errorCode
        tokenData["errorMessage"] = errorMessage
        tokenData["errorFlag"] = errorMessage is not None

        return tokenData
