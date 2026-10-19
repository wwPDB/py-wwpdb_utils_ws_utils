##
# File: ServiceSmtpUtilsTests.py
# Date:  17-Oct-2026
#
# Updates:
##
"""
Test cases for ServiceSmtpUtils class.  SMTP connections are mocked.

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""

__docformat__ = "restructuredtext en"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import base64
import email
import logging
import os
import tempfile
import unittest
from email.message import Message
from typing import List
from unittest import mock

from wwpdb.utils.ws_utils.ServiceSmtpUtils import ServiceSmtpUtils

logging.basicConfig(level=logging.DEBUG, format="\n[%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logging.getLogger().setLevel(logging.INFO)

SMTP_TARGET = "wwpdb.utils.ws_utils.ServiceSmtpUtils.smtplib.SMTP"
FROM_ADDR = "from@noreply.org"
TO_ADDR = "to@noreply.org"


class ServiceSmtpUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpdir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.__file1 = os.path.join(self.__tmpdir.name, "attach1.txt")
        with open(self.__file1, "w", encoding="utf-8") as ofh:
            ofh.write("attachment content\n")

    def tearDown(self) -> None:
        self.__tmpdir.cleanup()

    def __getSentMessage(self, mSmtp: mock.MagicMock) -> Message:
        inst = mSmtp.return_value
        inst.connect.assert_called_once_with()
        inst.close.assert_called_once_with()
        inst.sendmail.assert_called_once()
        args = inst.sendmail.call_args[0]
        self.assertEqual(args[0], FROM_ADDR)
        self.assertEqual(args[1], [TO_ADDR])
        return email.message_from_string(args[2])

    def __attachmentNames(self, msg: Message) -> List[str]:
        return [str(p.get_filename()) for p in msg.walk() if p.get_filename() is not None]

    def testEmailFiles(self) -> None:
        su = ServiceSmtpUtils()
        with mock.patch(SMTP_TARGET) as mSmtp:
            ok = su.emailFiles(
                FROM_ADDR,
                TO_ADDR,
                "Subject 1",
                "Body text",
                replyAddr="reply@noreply.org",
                fileList=[self.__file1],
                textAsAttachment="token-data",
                textAttachmentName="mytoken.txt",
            )
        self.assertTrue(ok)
        msg = self.__getSentMessage(mSmtp)
        self.assertEqual(msg["Subject"], "Subject 1")
        self.assertEqual(msg["reply-to"], "reply@noreply.org")
        self.assertEqual(self.__attachmentNames(msg), ["attach1.txt", "mytoken.txt"])
        for part in msg.walk():
            if part.get_filename() == "mytoken.txt":
                self.assertEqual(base64.b64decode(part.get_payload()), b"token-data")  # type: ignore[arg-type]

    def testEmailFilesMinimal(self) -> None:
        su = ServiceSmtpUtils()
        with mock.patch(SMTP_TARGET) as mSmtp:
            ok = su.emailFiles(FROM_ADDR, TO_ADDR, "Subject 2", "Body text")
        self.assertTrue(ok)
        msg = self.__getSentMessage(mSmtp)
        self.assertIsNone(msg["reply-to"])
        self.assertEqual(self.__attachmentNames(msg), [])

    def testEmailFilesFailure(self) -> None:
        su = ServiceSmtpUtils()
        with mock.patch(SMTP_TARGET) as mSmtp:
            mSmtp.return_value.connect.side_effect = OSError("no server")
            ok = su.emailFiles(FROM_ADDR, TO_ADDR, "Subject 3", "Body text")
        self.assertFalse(ok)

    def testEmailTextWithAttachment(self) -> None:
        su = ServiceSmtpUtils()
        with mock.patch(SMTP_TARGET) as mSmtp:
            ok = su.emailTextWithAttachment(
                FROM_ADDR,
                TO_ADDR,
                "reply@noreply.org",
                "Subject 4",
                "Body",
                textAsAttachment="abc",
                textFileName="/some/path/out.txt",
            )
        self.assertTrue(ok)
        msg = self.__getSentMessage(mSmtp)
        self.assertEqual(msg["Subject"], "Subject 4")
        self.assertEqual(self.__attachmentNames(msg), ["out.txt"])

    def testEmailTextNoAttachment(self) -> None:
        su = ServiceSmtpUtils()
        with mock.patch(SMTP_TARGET) as mSmtp:
            ok = su.emailTextWithAttachment(FROM_ADDR, TO_ADDR, "reply@noreply.org", "Subject 5", "Body")
        self.assertTrue(ok)
        msg = self.__getSentMessage(mSmtp)
        self.assertEqual(self.__attachmentNames(msg), [])

    def testEmailTextWithAttachmentFailure(self) -> None:
        su = ServiceSmtpUtils()
        with mock.patch(SMTP_TARGET) as mSmtp:
            mSmtp.return_value.sendmail.side_effect = OSError("send failed")
            ok = su.emailTextWithAttachment(FROM_ADDR, TO_ADDR, "reply@noreply.org", "Subject 6", "Body")
        self.assertFalse(ok)

    def testSendFile(self) -> None:
        su = ServiceSmtpUtils()
        with mock.patch(SMTP_TARGET) as mSmtp:
            su.sendFile(self.__file1, TO_ADDR, FROM_ADDR, "Subject 7")
        msg = self.__getSentMessage(mSmtp)
        self.assertEqual(msg["Subject"], "Subject 7")
        self.assertEqual(msg["From"], FROM_ADDR)
        self.assertEqual(msg["To"], TO_ADDR)
        self.assertEqual(msg["reply-to"], "noreply@mail.wwpdb.org")
        self.assertEqual(msg.get_payload(), "attachment content\n")

    def testSendFileNoReply(self) -> None:
        su = ServiceSmtpUtils()
        with mock.patch(SMTP_TARGET) as mSmtp:
            su.sendFile(self.__file1, TO_ADDR, FROM_ADDR, "Subject 8", replyAddr=None)
        msg = self.__getSentMessage(mSmtp)
        self.assertIsNone(msg["reply-to"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
