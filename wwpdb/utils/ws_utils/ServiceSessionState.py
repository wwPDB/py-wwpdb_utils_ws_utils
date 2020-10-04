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

logger = logging.getLogger()


class ServiceSessionState(object):
    """Accessors to encapsulate common service session details --"""

    #

    def __init__(self):
        """"""
        #
        self.__D = {}
        self.__strKeyList = ["servicename", "serviceargs", "statustext", "errormessage", "warningmessage", "responseformat"]
        #
        self.__boolKeyList = ["errorflag", "warningflag"]
        self.clear()
        #
        #  Containers for variable application data and files details-
        self.__A = {}
        self.__uFL = []
        self.__dFL = []
        #
        self.clear()

    #

    def clear(self):
        self.__A = {}
        self.__uFL = []
        self.__dFL = []
        self.__D = {}
        for ky in self.__strKeyList:
            self.__D[ky] = ""
        for ky in self.__boolKeyList:
            self.__D[ky] = False

    def setAppDataDict(self, dictval, errFlag=False, format="json"):  # pylint: disable=redefined-builtin
        try:
            self.__D["responseformat"] = format
            self.__D["errorflag"] = errFlag
            for k, v in dictval.items():
                self.__A[k] = v
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def setAppData(self, key, value):
        try:
            self.__A[key] = value
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def getAppDataDict(self):
        return self.__A

    def getUploadList(self):
        return self.__uFL

    def getDownloadList(self):
        return self.__dFL

    def setDownload(self, fileName, filePath, contentType=None, md5Digest=None):
        try:
            self.__dFL.append((fileName, filePath, contentType, md5Digest))
            self.__D["responseformat"] = "files"
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def setUpload(self, fileName, filePath, contentType=None, md5Digest=None):
        try:
            self.__uFL.append((fileName, filePath, contentType, md5Digest))
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def assign(self, name, args=None, completionFlag=None):
        try:
            if name is not None:
                self.setServiceName(name)
            if args is not None:
                self.setServiceArgs(args)
            if completionFlag is not None:
                self.setServiceCompletionFlag(completionFlag)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            logging.exception("FAILING")
            return False

    def setResponseFormat(self, format="json"):  # pylint: disable=redefined-builtin
        self.__D["responseformat"] = format

    def getResponseFormat(self):
        return self.__D["responseformat"]

    def setServiceName(self, name):
        self.__D["servicename"] = name

    def getServiceName(self):
        return self.__D["servicename"]

    def setServiceArgs(self, val):
        self.__D["serviceargs"] = val

    def getServiceArgs(self):
        return self.__D["serviceargs"]

    def setServiceStatusText(self, msg):
        self.__D["statustext"] = msg

    def getServiceStatusText(self):
        return self.__D["statustext"]

    def setServiceCompletionFlag(self, boolFlag):
        self.__D["errorflag"] = not boolFlag

    #
    def setServiceError(self, msg, errFlag=True, format="json"):  # pylint: disable=redefined-builtin
        self.__D["errorflag"] = errFlag
        self.__D["errormessage"] = msg
        self.__D["responseformat"] = format

    #

    def setServiceWarning(self, msg, warnFlag=True, format="json"):  # pylint: disable=redefined-builtin
        self.__D["warningflag"] = warnFlag
        self.__D["warningmessage"] = msg
        self.__D["responseformat"] = format

    def setServiceErrorFlag(self, boolFlag):
        self.__D["errorflag"] = boolFlag

    def getServiceErrorFlag(self):
        return self.__D["errorflag"]

    def setServiceWarningFlag(self, boolFlag):
        self.__D["warningflag"] = boolFlag

    def getServiceWarningFlag(self):
        return self.__D["warningflag"]

    def setServiceErrorMessage(self, msg):
        self.__D["errormessage"] = msg

    def getServiceErrorMessage(self):
        return self.__D["errormessage"]

    def setServiceWarningMessage(self, msg):
        self.__D["warningmessage"] = msg

    def getServiceWarningMessage(self):
        return self.__D["warningmessage"]


#
