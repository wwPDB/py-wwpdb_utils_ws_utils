##
# File:  ServiceSmtpUtils.py
# Date:  3-Aug-2016
#
# Updates:
#   3-Aug-2016 jdw  -- refactor from TokenUtils
##
"""
SMTP/Mail utilities

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
import os.path


import smtplib
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from email import encoders
from email.utils import formatdate


import logging

logger = logging.getLogger()


class ServiceSmtpUtils(object):
    def __init__(self):
        """Collection of mail handling methods -"""

    def sendFile(self, srcPath, toAddr, fromAddr, subject, replyAddr="noreply@mail.wwpdb.org"):
        """Internal method to mail file as text.

        Reply-To: noreply@example.com
        """

        # Create a text/plain message
        fp = open(srcPath, "rb")
        msg = MIMEText(fp.read())
        fp.close()
        #
        msg["Subject"] = subject
        msg["From"] = fromAddr
        msg["To"] = toAddr
        if replyAddr is not None:
            msg["reply-to"] = replyAddr

        #
        s = smtplib.SMTP()
        s.connect()
        s.sendmail(fromAddr, [toAddr], msg.as_string())
        s.close()

    def emailFiles(self, fromAddr, toAddr, subject, text, replyAddr=None, fileList=None, textAsAttachment=None, textAttachmentName="token.txt"):
        """'noreply@mail.wwpdb.org'"""

        msg = MIMEMultipart()
        msg["From"] = fromAddr
        msg["To"] = toAddr
        msg["Date"] = formatdate(localtime=True)
        msg["Subject"] = subject
        if replyAddr:
            msg["reply-to"] = replyAddr
        #
        msg.attach(MIMEText(text))

        for file in fileList or []:
            part = MIMEBase("application", "octet-stream")
            with open(file, "rb") as infile:
                part.set_payload(infile.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", 'attachment; filename="%s"' % os.path.basename(file))
            msg.attach(part)
        #
        if textAsAttachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(textAsAttachment)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", 'attachment; filename="%s"' % textAttachmentName)
            msg.attach(part)
        #
        try:
            s = smtplib.SMTP()
            s.set_debuglevel(1)
            s.connect()
            s.sendmail(fromAddr, [toAddr], msg.as_string())
            s.close()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILING")
        return False

    def emailTextWithAttachment(self, fromAddr, toAddr, replyAddr, subject, text, textAsAttachment=None, textFileName=None):
        """"""

        msg = MIMEMultipart()
        msg["From"] = fromAddr
        msg["To"] = toAddr
        msg["Date"] = formatdate(localtime=True)
        msg["Subject"] = subject
        msg["reply-to"] = replyAddr
        #
        msg.attach(MIMEText(text))

        if textAsAttachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(textAsAttachment)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", 'attachment; filename="%s"' % os.path.basename(textFileName))
            msg.attach(part)
        #
        try:
            s = smtplib.SMTP()
            s.set_debuglevel(1)
            s.connect()
            s.sendmail(fromAddr, [toAddr], msg.as_string())
            s.close()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILING")
        return False
