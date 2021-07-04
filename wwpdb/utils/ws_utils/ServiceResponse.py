##
# File:    ServiceResponse.py
# Date:    9-July-2016  J. Westbrook
#
# Updated:
#
##
"""
Containers and accessors for managing responses to web service requests.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import os
import gzip
import mimetypes
import logging
from webob import Response


try:
    import json
except ImportError:  # pragma: no cover
    import simplejson as json

try:
    # Python 2
    text_type = unicode
except NameError:
    # Python 3
    text_type = str

logger = logging.getLogger()


class ServiceResponse(object):
    def __init__(self, returnFormat="json", injectStatus=True):
        """
        Manage content items to be transfered as part of the application response.

        Set injectStatus=True to add statustext and errorflag to the data payload
          if these are not set.

        """
        self.__injectStatus = injectStatus
        self._cD = self.__setup(returnFormat)

    def __setup(self, returnFormat):
        """Default response content is set here."""
        cD = {}
        cD["returnformat"] = returnFormat
        cD["htmllinkcontent"] = ""
        cD["htmlcontent"] = ""
        cD["textcontent"] = ""
        cD["location"] = ""
        cD["contentmimetype"] = None
        cD["encodingtype"] = None
        cD["disposition"] = None
        #
        # Data payload container for file based data content
        cD["datafilecontent"] = None
        cD["datafilename"] = None
        cD["datafilechecksum"] = None
        #
        #  Data payload for all json objects -
        cD["datacontent"] = {}

        #  Status items
        cD["errorflag"] = False
        cD["statustext"] = ""
        cD["statuscode"] = 200
        #
        #
        return cD

    def isError(self):
        return self._cD["errorflag"]

    def setError(self, statusCode=200, msg=""):
        self._cD["errorflag"] = True
        self._cD["statustext"] = msg
        self._cD["statuscode"] = statusCode

    #
    def setData(self, dataObj=None):
        self._cD["datacontent"] = dataObj

    def getData(self):
        return self._cD["datacontent"]

    #
    def setHtmlList(self, htmlList=None):
        if htmlList is None:
            htmlList = []
        self._cD["htmlcontent"] = "\n".join(htmlList)

    def appendHtmlList(self, htmlList=None):
        if htmlList is None:
            htmlList = []
        if len(self._cD["htmlcontent"]) > 0:
            self._cD["htmlcontent"] = "%s\n%s" % (self._cD["htmlcontent"], "\n".join(htmlList))
        else:
            self._cD["htmlcontent"] = "\n".join(htmlList)

    def setHtmlText(self, htmlText=""):
        self._cD["htmlcontent"] = htmlText

    def setHtmlTextFromTemplate(self, templateFilePath, webIncludePath, parameterDict=None, insertContext=False):
        pD = parameterDict if parameterDict is not None else {}
        self._cD["htmlcontent"] = self.__processTemplate(templateFilePath=templateFilePath, webIncludePath=webIncludePath, parameterDict=pD, insertContext=insertContext)

    def setHtmlLinkText(self, htmlText=""):
        self._cD["htmllinkcontent"] = htmlText

    def setText(self, text=""):
        self._cD["textcontent"] = text

    def setLocation(self, url=""):
        self._cD["location"] = url

    def setTextFile(self, filePath):
        try:
            if os.path.exists(filePath):
                with open(filePath, "r") as fin:
                    self._cD["textcontent"] = fin.read()
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("+setTextFile() File read failed %s\n", filePath)

    def setHtmlContentPath(self, aPath):
        self._cD["htmlcontentpath"] = aPath

    def getMimetypeAndEncoding(self, filename):
        ftype, encoding = mimetypes.guess_type(filename)
        # We'll ignore encoding, even though we shouldn't really
        if ftype is None:
            if filename.find(".cif.V") > 0:
                ret = ("text/plain", None)
            else:
                ret = ("application/octet-stream", None)
        else:
            ret = (ftype, encoding)
        return ret

    def setBinaryFile(self, filePath, attachmentFlag=False, serveCompressed=True, md5Digest=None):
        try:
            if os.path.exists(filePath):
                _dir, fn = os.path.split(filePath)
                if not serveCompressed and fn.endswith(".gz"):
                    with gzip.open(filePath, "rb") as fin:
                        self._cD["datafilecontent"] = fin.read()
                    self._cD["datafileName"] = fn[:-3]
                    contentType, encodingType = self.getMimetypeAndEncoding(filePath[:-3])
                else:
                    with open(filePath, "rb") as fin:
                        self._cD["datafilecontent"] = fin.read()
                    self._cD["datafileName"] = fn
                    contentType, encodingType = self.getMimetypeAndEncoding(filePath)
                #
                self._cD["contentmimetype"] = contentType
                self._cD["encodingtype"] = encodingType
                if attachmentFlag:
                    self._cD["disposition"] = "attachment"
                else:
                    self._cD["disposition"] = "inline"
                    #
                    # strip compression file extension if disposition=inline.
                    if fn.endswith(".gz"):
                        self._cD["datafileName"] = fn[:-3]
                if md5Digest:
                    self._cD["datafilechecksum"] = md5Digest
                logger.debug("Serving %s as %s encoding %s att flag %r checksum %r\n", filePath, contentType, encodingType, attachmentFlag, md5Digest)
                return True
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("ResponseContent.setBinaryFile() File read failed %s\n", filePath)
        return False

    def wrapFileAsJsonp(self, filePath, callBack=None):
        try:
            if os.path.exists(filePath):
                _dir, fn = os.path.split(filePath)
                (_rn, ext) = os.path.splitext(fn)
                #
                dd = {}
                with open(filePath, "r") as fin:
                    dd["data"] = fin.read()
                if ext.lower() != ".json":
                    self._cD["datafilecontent"] = callBack + "(" + json.dumps(dd) + ");"
                else:
                    self._cD["datafilecontent"] = callBack + "(" + dd["data"] + ");"
                #
                self._cD["datafileName"] = fn
                contentType = "application/x-javascript"
                encodingType = None
                #
                self._cD["contentmimetype"] = contentType
                self._cD["encodingtype"] = encodingType
                self._cD["disposition"] = "inline"
                #

                logger.debug("Serving %s as %s\n", filePath, self._cD["datafilecontent"])
        except Exception as e:
            logging.exception("File read failed %s err %r", filePath, str(e))

    def dump(self, maxLength=130):
        retL = []
        retL.append("Service response object:")
        for k, v in self._cD.items():
            if v is None:
                continue
            elif isinstance(v, dict):
                retL.append("  - key = %-35s - dict : %s" % (k, v.items()))
            elif v is not None and len(str(v).strip()) > 0:
                retL.append("  - key = %-35s - value(1-%d): %s" % (k, maxLength, str(v)[:maxLength]))
        return "\n   ".join(retL)

    def setReturnFormat(self, format):  # pylint: disable=redefined-builtin
        if format in ["html", "text", "json", "jsonText", "jsonData", "location", "binary", "jsonp"]:
            self._cD["returnformat"] = format
            return True
        else:
            return False

    def __injectMessage(self, tag, msg):
        try:
            if tag not in self._cD["datacontent"]:
                self._cD["datacontent"][tag] = msg
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return False

    def getResponse(self):
        rspD = self.__getD()
        #
        #  Build the WebOb response -
        #
        myResponse = Response()
        myResponse.status = rspD["STATUS_CODE"]
        myResponse.content_type = rspD["CONTENT_TYPE"]

        if isinstance(rspD["RETURN_STRING"], text_type):
            myResponse.text = rspD["RETURN_STRING"]
        else:
            myResponse.body = rspD["RETURN_STRING"]

        if "ENCODING" in rspD:
            myResponse.content_encoding = rspD["ENCODING"]
        if "DISPOSITION" in rspD:
            myResponse.content_disposition = rspD["DISPOSITION"]
        if "CHECKSUM_MD5" in rspD:
            myResponse.headers.add("CHECKSUM_MD5", rspD["CHECKSUM_MD5"])
        #
        return myResponse

    def __getD(self):
        """Return an internal dictionary as precursor to preparing for web server response object"""
        rD = {}
        returnFormat = self._cD["returnformat"]

        #
        # Handle error cases --
        #
        if self._cD["errorflag"]:
            if returnFormat in ["json", "jsonText", "jsonData", "jsonp"]:
                if self.__injectStatus:
                    self.__injectMessage("statustext", self._cD["statustext"])
                    self.__injectMessage("errorflag", self._cD["errorflag"])

                rD = self.__initJsonResponse(self._cD["datacontent"])
            elif returnFormat in ["html", "location"]:
                rD = self.__initHtmlResponse(self._cD["statustext"])
            elif returnFormat in ["text", "binary"]:
                rD = self.__initTextResponse(self._cD["statustext"])
            else:
                rD = self.__initTextResponse(self._cD["statustext"])
        else:
            #
            if returnFormat == "html":
                rD = self.__initHtmlResponse(self._cD["htmlcontent"])
            #
            elif returnFormat == "text":
                rD = self.__initTextResponse(self._cD["textcontent"])
            #
            elif returnFormat == "location":
                rD = self.__initLocationResponse(self._cD["location"])
            #
            elif returnFormat == "jsonText":
                rD = self.__initJsonResponseInTextArea(self._cD["datacontent"])
            #
            elif returnFormat == "json":
                rD = self.__initJsonResponse(self._cD["datacontent"])
            #
            elif returnFormat == "jsonData":
                rD = self.__initJsonResponse(self._cD["datacontent"])
            #
            elif returnFormat == "binary":
                rD = self.__initBinaryResponse(self._cD)
                if self._cD["datafilechecksum"]:
                    rD["CHECKSUM_MD5"] = self._cD["datafilechecksum"]
            #
            elif returnFormat == "jsonp":
                rD = self.__initJsonpResponse(self._cD)
            else:
                pass
        #
        rD["STATUS_CODE"] = self._cD["statuscode"]
        return rD

    def __initLocationResponse(self, url):
        rspDict = {}
        rspDict["CONTENT_TYPE"] = "location"
        rspDict["RETURN_STRING"] = url
        return rspDict

    def __initBinaryResponse(self, myD=None):
        if myD is None:
            myD = {}
        rspDict = {}
        rspDict["CONTENT_TYPE"] = myD["contentmimetype"]
        rspDict["RETURN_STRING"] = myD["datafilecontent"]
        try:  # noqa: E722 pylint: disable=bare-except
            rspDict["ENCODING"] = myD["encodingtype"]
            if myD["disposition"] is not None:
                rspDict["DISPOSITION"] = "%s; filename=%s" % (myD["disposition"], myD["datafileName"])
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return rspDict

    def __initJsonResponse(self, myD=None):
        if myD is None:
            myD = {}
        rspDict = {}
        rspDict["CONTENT_TYPE"] = "application/json"
        rspDict["RETURN_STRING"] = json.dumps(myD)
        return rspDict

    def __initJsonpResponse(self, myD=None):
        if myD is None:
            myD = {}
        rspDict = {}
        rspDict["CONTENT_TYPE"] = myD["contentmimetype"]
        rspDict["RETURN_STRING"] = myD["datafilecontent"]
        return rspDict

    def __initJsonResponseInTextArea(self, myD=None):
        if myD is None:
            myD = {}
        rspDict = {}
        rspDict["CONTENT_TYPE"] = "text/html"
        rspDict["RETURN_STRING"] = "<textarea>" + json.dumps(myD) + "</textarea>"
        return rspDict

    def __initHtmlResponse(self, myHtml=""):
        rspDict = {}
        rspDict["CONTENT_TYPE"] = "text/html"
        rspDict["RETURN_STRING"] = myHtml
        return rspDict

    def __initTextResponse(self, myText=""):
        rspDict = {}
        rspDict["CONTENT_TYPE"] = "text/plain"
        rspDict["RETURN_STRING"] = myText
        return rspDict

    def __processTemplate(self, templateFilePath="./alignment_template.html", webIncludePath=".", parameterDict=None, insertContext=False):
        """Read the input HTML template data file and perform the key/value substitutions in the
        input parameter dictionary.

        if insertContext is set then paramDict is injected as a json object if <!--insert application_context=""-->

        Template HTML file path -  (e.g. /../../htdocs/<appName>/template.html)
        webTopPath = file system path for web includes files  (eg. /../../htdocs) which will
                     be prepended to embedded include path in the HTML template document
        """

        if parameterDict is None:
            parameterDict = {}
        try:
            ifh = open(templateFilePath, "r")
            sL = []
            for line in ifh.readlines():
                if str(line).strip().startswith("<!--#include") or (insertContext and str(line).strip().startswith("<!--#insert")):
                    fields = str(line).split('"')
                    tpth = os.path.join(webIncludePath, fields[1][1:])
                    try:
                        tfh = open(tpth, "r")
                        sL.append(tfh.read())
                        tfh.close()
                    except Exception as e:
                        logger.debug("failed to include %s fields=%r err=%r\n", tpth, fields, str(e))
                else:
                    sL.append(line)
            ifh.close()
            sIn = "".join(sL)
            return sIn % parameterDict
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Failed for %s\n", templateFilePath)

        return ""
