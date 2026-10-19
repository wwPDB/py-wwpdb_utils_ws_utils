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

import datetime
import logging
import os
import pickle  # noqa: S403
import sys
from typing import Any, Dict, Optional, Tuple

import jwt
from oslo_concurrency import lockutils
from wwpdb.utils.config.ConfigInfo import ConfigInfo

logger = logging.getLogger()


class TokenUtilsBase:
    def __init__(self, siteId: Optional[str] = None, tokenPrefix: Optional[str] = None, **kwargs: Any) -> None:
        """
        Base class supporting application token management in persistent store.
        kwargs allows for overriding ConfigInfo for testing

        """
        self._cI = ConfigInfo(siteId)
        if tokenPrefix is not None:
            fn = tokenPrefix + "_TOKEN_STORE.pic"
        else:
            fn = "ANONYMOUSWS_TOKEN_STORE.pic"
        self.__filePath: str = kwargs.get("site_service_registration_dir_path", "")
        if not self.__filePath:
            self.__filePath = os.path.join(self._cI.get("SITE_SERVICE_REGISTRATION_DIR_PATH"), fn)
        logger.debug("Assigning token store file path %r", self.__filePath)
        self.__lockDirPath: str = kwargs.get("site_service_registration_lockdir_path", "")
        if not self.__lockDirPath:
            self.__lockDirPath = self._cI.get("SITE_SERVICE_REGISTRATION_LOCKDIR_PATH", ".")
        self.__tokenD: Dict[str, Dict[str, Any]] = {}
        self.__emailD: Dict[str, str] = {}
        self.__tokenPrefix = tokenPrefix or "WS"
        self.__pickleProtocol = 0
        lockutils.set_defaults(self.__lockDirPath)
        self.deserialize()

    def __makeTokenId(self, iVal: int) -> str:
        return "%s_%010d" % (self.__tokenPrefix, iVal)

    def __parseTokenId(self, tokenId: str) -> Tuple[Optional[str], Optional[int]]:
        try:
            pL = tokenId.split("_")
            prefix = pL[0]
            iVal = int(pL[1])
            return (prefix, iVal)
        except:  # noqa: E722 pylint: disable=bare-except
            return (None, None)

    def getFilePath(self) -> str:
        return self.__filePath

    @lockutils.synchronized("tokenutils.serialize-lock", external=True)
    def serialize(self) -> bool:
        try:
            with open(self.__filePath, "wb") as outfile:
                pickle.dump(self.__tokenD, outfile, self.__pickleProtocol)
                pickle.dump(self.__emailD, outfile, self.__pickleProtocol)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILING")
        return False

    def deserialize(self) -> bool:
        try:
            with open(self.__filePath, "rb") as outfile:
                self.__tokenD = pickle.load(outfile)  # noqa: S301
                self.__emailD = pickle.load(outfile)  # noqa: S301
            logger.debug("Recovered %4d token Ids %4d e-mails", len(self.__tokenD), len(self.__emailD))
            return True
        except Exception as e:  # noqa: BLE001
            logger.debug("Unable to deserialize persistent token store %r - %r", self.__filePath, str(e))
        return False

    def tokenIdExists(self, tokenId: str) -> bool:
        try:
            return tokenId in self.__tokenD
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return False

    def tokenIdEmailExists(self, email: str) -> bool:
        try:
            return email in self.__emailD
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return False

    @lockutils.synchronized("tokenutils.transaction-lock", external=True)
    def remove(self, tokenId: str) -> bool:
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

    def getTokenIdEmail(self, tokenId: str) -> str:
        try:
            return str(self.__tokenD[tokenId]["email"])
        except:  # noqa: E722 pylint: disable=bare-except
            return ""

    def saveTokenId(self, tokenId: Optional[str], email: Optional[str], **kw: Any) -> bool:
        """"""
        if tokenId is None or len(tokenId) < 12 or email is None or len(email) < 3:
            return False
        try:
            tD: Dict[str, Any] = {"email": email}
            tD.update(kw)
            self.__tokenD[tokenId] = tD
            self.__emailD[email] = tokenId
            self.serialize()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Token save FAILING")
        return False

    def fetchTokenId(self, email: str) -> str:
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

    def __nextTokenId(self) -> int:
        """Return the next token identifier string (e.g. N+1 for <PREFIX>_0000000N)

        return 1-N for success or -1 for failure
        """
        try:
            if len(self.__tokenD.keys()) > 0:
                tokenMax = max(self.__tokenD.keys())
                _pr, tV = self.__parseTokenId(tokenMax)
                if tV is None:
                    raise ValueError("Unable to parse token id %r" % tokenMax)
                iV = tV + 1
            else:
                iV = 1
            return iV
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILING")

        return -1


class JwtTokenUtils(TokenUtilsBase):
    def __init__(self, siteId: Optional[str] = None, tokenPrefix: Optional[str] = None, **kwargs: Any) -> None:
        """
        Token utilities for registration webservice

        """
        super(JwtTokenUtils, self).__init__(siteId=siteId, tokenPrefix=tokenPrefix, **kwargs)
        #
        # self.__inputToken = self._reqObj.getValue('authorization').split()[1]
        #
        serviceKey = self._cI.get("SITE_SERVICE_REGISTRATION_KEY", None)
        self.__serviceKey: str = serviceKey or "secretvalue"
        self.__tokenErrorCode = 401

    def parseAuth(self, authHeader: str) -> Dict[str, Any]:
        rD: Dict[str, Any] = {"errorCode": None, "errorMessage": None, "token": None, "errorFlag": False}
        parts = authHeader.split()
        if parts[0].lower() != "bearer":
            rD = {
                "errorCode": self.__tokenErrorCode,
                "errorMessage": "Authorization header must start with Bearer",
                "errorFlag": True,
            }
        elif len(parts) == 1:
            rD = {"errorCode": self.__tokenErrorCode, "errorMessage": "API access token not found", "errorFlag": True}
        elif len(parts) > 2:
            rD = {
                "errorCode": self.__tokenErrorCode,
                "errorMesage": "Authorization header must be Bearer token",
                "errorFlag": True,
            }
        if not rD["errorFlag"]:
            rD["token"] = parts[1]
        return rD

    def parseToken(self, token: Optional[str]) -> Dict[str, Any]:
        """Return data payload for the input token along with any error diagnostics -"""
        return self.__getTokenData(token)

    def getToken(self, email: str, expireDays: int = 30) -> Tuple[str, str]:
        """Return a tokenId and a jwt token for the input e-mail address.
        Existing tokenId's are reused with the existing email address.

        """
        tokenId = self.fetchTokenId(email)
        jwtToken = self.__create_token(tokenId, self.__serviceKey, expireDays=expireDays)
        return tokenId, jwtToken

    def __getutcnow(self) -> datetime.datetime:
        """Returns timezone aware utc now if system allows"""
        if sys.version_info[0] > 2:  # noqa: UP036
            dtNow = datetime.datetime.now(datetime.timezone.utc)
        else:
            dtNow = datetime.datetime.utcnow()  # noqa: DTZ003
        return dtNow

    def __create_token(
        self, tokenId: str, secretKey: str, expireDays: int = 30, algorithm: str = "HS256", encoding: str = "utf-8"
    ) -> str:
        payload = {
            #        using the standard JWT claim keys --
            # subject id
            "sub": tokenId,
            # creation datetime
            "iat": self.__getutcnow(),
            # expiration datetime
            "exp": self.__getutcnow() + datetime.timedelta(days=expireDays),
        }
        token = jwt.encode(payload, secretKey, algorithm=algorithm)
        #
        # PyJwt 2.x return string, 1.x returns bytes
        #
        if isinstance(token, bytes):
            #
            # 'utf-8' or 'unicode_escape'?
            #
            return token.decode(encoding)
        return token

    def __parseToken(
        self, token: Optional[str], secretKey: str = "secretvalue", algorithm: str = "HS256"
    ) -> Dict[str, Any]:
        # A missing token is rejected by jwt.decode() as invalid
        return jwt.decode(token or "", secretKey, algorithms=[algorithm])

    def __getTokenData(self, token: Optional[str]) -> Dict[str, Any]:
        """Return token payload as a dictionary and processing diagnostics -"""
        errorCode = None
        errorMessage = None
        tokenData: Dict[str, Any] = {}
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


class JwtTokenReader:
    def __init__(self, siteId: Optional[str] = None) -> None:
        """
        Limited set of token methods required to read and validate a JWT tokens.

        """
        self._cI = ConfigInfo(siteId)
        serviceKey = self._cI.get("SITE_SERVICE_REGISTRATION_KEY", default=None)
        self.__serviceKey: str = serviceKey or "secretvalue"
        self.__tokenErrorCode = 401

    def parseAuth(self, authHeader: str) -> Dict[str, Any]:
        rD: Dict[str, Any] = {"errorCode": None, "errorMessage": None, "token": None, "errorFlag": False}
        parts = authHeader.split()
        if parts[0].lower() != "bearer":
            rD = {
                "errorCode": self.__tokenErrorCode,
                "errorMessage": "Authorization header must start with Bearer",
                "errorFlag": True,
            }
        elif len(parts) == 1:
            rD = {"errorCode": self.__tokenErrorCode, "errorMessage": "API access token not found", "errorFlag": True}
        elif len(parts) > 2:
            rD = {
                "errorCode": self.__tokenErrorCode,
                "errorMesage": "Authorization header must be Bearer token",
                "errorFlag": True,
            }
        if not rD["errorFlag"]:
            rD["token"] = parts[1]
        return rD

    def parseToken(self, token: Optional[str]) -> Dict[str, Any]:
        """Return data payload for the input token along with any error diagnostics -"""
        return self.__getTokenData(token)

    def __parseToken(
        self, token: Optional[str], secretKey: str = "secretvalue", algorithm: str = "HS256"
    ) -> Dict[str, Any]:
        # A missing token is rejected by jwt.decode() as invalid
        return jwt.decode(token or "", secretKey, algorithms=[algorithm])

    def __getTokenData(self, token: Optional[str]) -> Dict[str, Any]:
        """Return token payload as a dictionary and processing diagnostics -"""
        errorCode = None
        errorMessage = None
        tokenData: Dict[str, Any] = {}
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
