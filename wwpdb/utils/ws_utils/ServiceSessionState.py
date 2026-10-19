##
# File:  ServiceSessionState
# Date:  2-July-2016
#
# Updated:
#         5-Aug-2016  jdw add support for application data
##
"""
Accessors to encapsulate common service session data management details --

"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import logging
from typing import Any, Dict, List, Optional, Tuple, TypedDict

logger = logging.getLogger()

# (fileName, filePath, contentType, md5Digest)
FileDetailTuple = Tuple[str, str, Optional[str], Optional[str]]


class _SessionStatusDict(TypedDict):
    servicename: str
    serviceargs: Any
    statustext: str
    errormessage: str
    warningmessage: str
    responseformat: str
    errorflag: bool
    warningflag: bool


class ServiceSessionState:
    """Accessors to encapsulate common service session details --"""

    def __init__(self) -> None:
        """"""
        #
        #  Containers for variable application data and files details-
        self.__A: Dict[str, Any] = {}
        self.__uFL: List[FileDetailTuple] = []
        self.__dFL: List[FileDetailTuple] = []
        self.__D: _SessionStatusDict = self.__newStatus()

    @staticmethod
    def __newStatus() -> _SessionStatusDict:
        return {
            "servicename": "",
            "serviceargs": "",
            "statustext": "",
            "errormessage": "",
            "warningmessage": "",
            "responseformat": "",
            "errorflag": False,
            "warningflag": False,
        }

    def clear(self) -> None:
        self.__A = {}
        self.__uFL = []
        self.__dFL = []
        self.__D = self.__newStatus()

    def setAppDataDict(
        self,
        dictval: Dict[str, Any],
        errFlag: bool = False,
        format: str = "json",  # noqa: A002 pylint: disable=redefined-builtin
    ) -> bool:
        try:
            self.__D["responseformat"] = format
            self.__D["errorflag"] = errFlag
            for k, v in dictval.items():
                self.__A[k] = v
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def setAppData(self, key: str, value: Any) -> bool:
        try:
            self.__A[key] = value
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def getAppDataDict(self) -> Dict[str, Any]:
        return self.__A

    def getUploadList(self) -> List[FileDetailTuple]:
        return self.__uFL

    def getDownloadList(self) -> List[FileDetailTuple]:
        return self.__dFL

    def setDownload(
        self, fileName: str, filePath: str, contentType: Optional[str] = None, md5Digest: Optional[str] = None
    ) -> bool:
        try:
            self.__dFL.append((fileName, filePath, contentType, md5Digest))
            self.__D["responseformat"] = "files"
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def setUpload(
        self, fileName: str, filePath: str, contentType: Optional[str] = None, md5Digest: Optional[str] = None
    ) -> bool:
        try:
            self.__uFL.append((fileName, filePath, contentType, md5Digest))
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def assign(self, name: Optional[str], args: Any = None, completionFlag: Optional[bool] = None) -> bool:
        try:
            if name is not None:
                self.setServiceName(name)
            if args is not None:
                self.setServiceArgs(args)
            if completionFlag is not None:
                self.setServiceCompletionFlag(completionFlag)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILING")
            return False

    def setResponseFormat(self, format: str = "json") -> None:  # noqa: A002 pylint: disable=redefined-builtin
        self.__D["responseformat"] = format

    def getResponseFormat(self) -> str:
        return self.__D["responseformat"]

    def setServiceName(self, name: str) -> None:
        self.__D["servicename"] = name

    def getServiceName(self) -> str:
        return self.__D["servicename"]

    def setServiceArgs(self, val: Any) -> None:
        self.__D["serviceargs"] = val

    def getServiceArgs(self) -> Any:
        return self.__D["serviceargs"]

    def setServiceStatusText(self, msg: str) -> None:
        self.__D["statustext"] = msg

    def getServiceStatusText(self) -> str:
        return self.__D["statustext"]

    def setServiceCompletionFlag(self, boolFlag: bool) -> None:
        self.__D["errorflag"] = not boolFlag

    def setServiceError(
        self,
        msg: str,
        errFlag: bool = True,
        format: str = "json",  # noqa: A002 pylint: disable=redefined-builtin
    ) -> None:
        self.__D["errorflag"] = errFlag
        self.__D["errormessage"] = msg
        self.__D["responseformat"] = format

    def setServiceWarning(
        self,
        msg: str,
        warnFlag: bool = True,
        format: str = "json",  # noqa: A002 pylint: disable=redefined-builtin
    ) -> None:
        self.__D["warningflag"] = warnFlag
        self.__D["warningmessage"] = msg
        self.__D["responseformat"] = format

    def setServiceErrorFlag(self, boolFlag: bool) -> None:
        self.__D["errorflag"] = boolFlag

    def getServiceErrorFlag(self) -> bool:
        return self.__D["errorflag"]

    def setServiceWarningFlag(self, boolFlag: bool) -> None:
        self.__D["warningflag"] = boolFlag

    def getServiceWarningFlag(self) -> bool:
        return self.__D["warningflag"]

    def setServiceErrorMessage(self, msg: str) -> None:
        self.__D["errormessage"] = msg

    def getServiceErrorMessage(self) -> str:
        return self.__D["errormessage"]

    def setServiceWarningMessage(self, msg: str) -> None:
        self.__D["warningmessage"] = msg

    def getServiceWarningMessage(self) -> str:
        return self.__D["warningmessage"]
