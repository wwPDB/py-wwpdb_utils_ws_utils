##
# File:  WebUploadUtils.py
# Date:  28-Feb-2013
#
# Updates:
#  28-Feb-2013   jdw imported common functions from WebApp(*).py  modules.
#  03-Mar-2013   jdw catch unicode type in empty file request.
#  28-Feb-2014   jdw add rename and file extension methods
#   2-Apr-2014   jdw add version flag to getFileExtension(fileName,ignoreVersion=False)
#  14-Sep-2014   jdw add getUploadFileName():
##
"""
Utilities to manage  web application upload tasks.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.09"

import sys
import ntpath
import os
import types
import shutil
import logging

logger = logging.getLogger()


class ServiceUploadUtils(object):
    """
    This class encapsulates all of the web application upload tasks.

    """

    def __init__(self, reqObj=None):
        self.__reqObj = reqObj
        #
        self.__sessionObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sessionObj.getPath()
        #
        logger.debug(" - session id   %s\n", self.__sessionObj.getId())
        logger.debug(" - session path %s\n", self.__sessionPath)

    def isFileUpload(self, fileTag="file"):
        """Generic check for the existence of request paramenter "fileTag="."""
        # Gracefully exit if no file is provide in the request object -
        fs = self.__reqObj.getRawValue(fileTag)

        logger.debug("+WebUploadUtils.isFileUpLoad() fs  %r", fs)
        if sys.version_info[0] < 3:
            if (fs is None) or (isinstance(fs, types.StringType)) or (isinstance(fs, types.UnicodeType)):  # noqa: E722 pylint: disable=no-member
                return False
        else:
            if (fs is None) or (isinstance(fs, str)) or (isinstance(fs, bytes)):
                return False
        return True

    def getUploadFileName(self, fileTag="file"):
        """Get the user supplied name of for the uploaded file -"""
        #

        logger.debug("operation started")
        #
        try:
            fs = self.__reqObj.getRawValue(fileTag)

            logger.debug("- upload file descriptor fs =     %r", fs)
            logger.debug("- upload file descriptor fs =     %s", fs)
            formRequestFileName = str(fs.filename).strip()

            #
            if formRequestFileName.find("\\") != -1:
                uploadInputFileName = ntpath.basename(formRequestFileName)
            else:
                uploadInputFileName = os.path.basename(formRequestFileName)

            logger.debug(" uploaded file name %s", str(uploadInputFileName))
            #
            return uploadInputFileName
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("+WebUploadUtils.getUploadFileName() processing failed")

        return None

    def copyToSession(self, fileTag="file", sessionFileName=None, uncompress=True):
        """Copy uploaded file identified form element name 'fileTag' to the current session directory.

        File is copied to user uploaded file or to the sessionFileName if this is provided.
        """
        #
        logger.debug("- operation started")
        #
        try:
            fs = self.__reqObj.getRawValue(fileTag)

            logger.debug("- upload file descriptor fs =     %r\n", fs)
            # formRequestFileName = str(fs.filename).strip().lower()
            formRequestFileName = str(fs.filename).strip()

            #
            if formRequestFileName.find("\\") != -1:
                uploadInputFileName = ntpath.basename(formRequestFileName)
            else:
                uploadInputFileName = os.path.basename(formRequestFileName)

            #
            # Copy uploaded file in session directory
            #
            if sessionFileName is not None:
                sessionInputFileName = sessionFileName
            else:
                sessionInputFileName = uploadInputFileName

            sessionInputFilePath = os.path.join(self.__sessionPath, sessionInputFileName)

            logger.debug("- user request file name     %s", fs.filename)
            logger.debug("- upload input file name     %s", uploadInputFileName)
            logger.debug("- session target file path   %s", sessionInputFilePath)
            logger.debug("- session target file name   %s", sessionInputFileName)
            #
            with open(sessionInputFilePath, "wb") as outfile:
                outfile.write(fs.file.read())
            #
            if uncompress and sessionInputFilePath.endswith(".gz"):

                logger.debug("-uncompressing file %s", str(sessionInputFilePath))
                self.__copyGzip(sessionInputFilePath, sessionInputFilePath[:-3])
                sessionInputFileName = sessionInputFileName[:-3]

            logger.debug("Uploaded file %s", str(sessionInputFileName))
            #
            return sessionInputFileName
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("File upload processing failed")
        return None

    def renameSessionFile(self, srcFileName, dstFileName):
        try:
            if srcFileName != dstFileName:
                srcPath = os.path.join(self.__sessionPath, srcFileName)
                dstPath = os.path.join(self.__sessionPath, dstFileName)
                shutil.copyfile(srcPath, dstPath)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def getFileExtension(self, fileName, ignoreVersion=False):
        """Return the file extension (basename.ext).

        If the input file contains no '.' then None is returned.

        if ignoreVersion=True then any trailing version details are
           discarded before extracting the file extension -
        """
        fExt = None
        if fileName is None or len(fileName) < 1:
            return fExt

        try:
            fL = str(fileName).split(".")
            if len(fL) < 2:
                return fExt

            if ignoreVersion and len(fL) > 2:
                tExt = fL[-1]
                if (tExt.startswith("V") or tExt.startswith("v")) and tExt[1:].isdigit():
                    fExt = fL[-2]
                else:
                    fExt = tExt
            else:
                if len(fL) > 1:
                    fExt = fL[-1]
        except:  # noqa: E722 pylint: disable=bare-except
            pass

        return fExt

    def perceiveIdentifier(self, fileName):
        """Return the file identifier and identifier source if these can be deduced from
        the input file name.   Returned values are in uppercase.
        """
        #
        #
        fId = None
        fType = None
        if fileName is None or len(fileName) < 1:
            return fId, fType

        (head, _tail) = os.path.splitext(str(fileName))
        headLC = head.upper()
        if headLC.startswith("RCSB"):
            fId = head
            fType = "RCSB"
        elif headLC.startswith("D_"):
            fId = head
            fType = "WF_ARCHIVE"
            #
            # Look for
            #
            fields = head.split("_")
            if len(fields) > 1:
                fId = "_".join(fields[:2])
        elif headLC.startswith("W_"):
            fId = head
            fType = "WF_INSTANCE"
        else:
            fId = head
            fType = "UNKNOWN"

            logger.debug("using non-standard identifier %r for %r", head, str(fileName))

        logger.debug("using identifier fId %r and file source %r", fId, fType)

        return fId, fType

    def __copyGzip(self, inpFilePath, outFilePath):
        """"""
        try:
            cmd = " gzip -cd  %s > %s " % (inpFilePath, outFilePath)
            os.system(cmd)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("uncompress failing")
        return False
