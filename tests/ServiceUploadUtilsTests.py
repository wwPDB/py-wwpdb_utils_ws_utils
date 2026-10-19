##
# File: ServiceUploadUtilsTests.py
# Date:  17-Oct-2026
#
# Updates:
##
"""
Test cases for ServiceUploadUtils class --

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""

__docformat__ = "restructuredtext en"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import gzip
import io
import logging
import os
import tempfile
import unittest
from typing import Optional

from wwpdb.utils.ws_utils.ServiceRequest import ServiceRequest
from wwpdb.utils.ws_utils.ServiceUploadUtils import ServiceUploadUtils

logging.basicConfig(level=logging.DEBUG, format="\n[%(levelname)s]-%(module)s.%(funcName)s: %(message)s")
logging.getLogger().setLevel(logging.INFO)


class FakeUpload:
    """Minimal stand-in for an uploaded form field (e.g. cgi.FieldStorage)"""

    def __init__(self, filename: str, data: bytes) -> None:
        self.filename = filename
        self.file = io.BytesIO(data)


class ServiceUploadUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpdir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        req = ServiceRequest({"top_session_path": [self.__tmpdir.name], "service_user_id": ["user1"]})
        sObj = req.getSessionObj(new=True)
        sessionPath: Optional[str] = sObj.getPath()
        assert sessionPath is not None  # noqa: S101
        self.__sessionPath = sessionPath
        self.__req = req

    def tearDown(self) -> None:
        self.__tmpdir.cleanup()

    def testIsFileUpload(self) -> None:
        self.__req.setValue("file", FakeUpload("a.txt", b"data"))
        self.__req.setValue("strfile", "notafile")
        self.__req.setValue("bytesfile", b"notafile")
        uu = ServiceUploadUtils(self.__req)
        self.assertTrue(uu.isFileUpload())
        self.assertFalse(uu.isFileUpload("strfile"))
        self.assertFalse(uu.isFileUpload("bytesfile"))

    def testGetUploadFileName(self) -> None:
        self.__req.setValue("file", FakeUpload("/some/path/a.txt", b"data"))
        self.__req.setValue("winfile", FakeUpload("C:\\Users\\me\\b.cif", b"data"))
        uu = ServiceUploadUtils(self.__req)
        self.assertEqual(uu.getUploadFileName(), "a.txt")
        self.assertEqual(uu.getUploadFileName("winfile"), "b.cif")
        # Missing upload
        self.assertIsNone(uu.getUploadFileName("missing"))

    def testCopyToSession(self) -> None:
        self.__req.setValue("file", FakeUpload("/some/path/a.txt", b"data1"))
        self.__req.setValue("winfile", FakeUpload("C:\\Users\\me\\b.cif", b"data2"))
        uu = ServiceUploadUtils(self.__req)

        self.assertEqual(uu.copyToSession(), "a.txt")
        with open(os.path.join(self.__sessionPath, "a.txt"), "rb") as ifh:
            self.assertEqual(ifh.read(), b"data1")

        self.assertEqual(uu.copyToSession(fileTag="winfile", sessionFileName="renamed.cif"), "renamed.cif")
        with open(os.path.join(self.__sessionPath, "renamed.cif"), "rb") as ifh:
            self.assertEqual(ifh.read(), b"data2")

        self.assertIsNone(uu.copyToSession(fileTag="missing"))

    def testCopyToSessionGzip(self) -> None:
        self.__req.setValue("file", FakeUpload("model.cif.gz", gzip.compress(b"compressed data")))
        uu = ServiceUploadUtils(self.__req)
        self.assertEqual(uu.copyToSession(), "model.cif")
        self.assertTrue(os.path.exists(os.path.join(self.__sessionPath, "model.cif.gz")))
        with open(os.path.join(self.__sessionPath, "model.cif"), "rb") as ifh:
            self.assertEqual(ifh.read(), b"compressed data")

    def testCopyToSessionGzipShellMetacharacters(self) -> None:
        """Upload file names must never be interpreted by a shell"""
        cwdDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(cwdDir.cleanup)
        oldCwd = os.getcwd()
        os.chdir(cwdDir.name)
        self.addCleanup(os.chdir, oldCwd)

        uploadName = "x;touch pwned;$(touch pwned2).gz"
        self.__req.setValue("file", FakeUpload(uploadName, gzip.compress(b"payload")))
        uu = ServiceUploadUtils(self.__req)
        self.assertEqual(uu.copyToSession(), uploadName[:-3])
        self.assertFalse(os.path.exists(os.path.join(cwdDir.name, "pwned")))
        self.assertFalse(os.path.exists(os.path.join(cwdDir.name, "pwned2")))
        with open(os.path.join(self.__sessionPath, uploadName[:-3]), "rb") as ifh:
            self.assertEqual(ifh.read(), b"payload")

    def testCopyToSessionGzipCorrupt(self) -> None:
        self.__req.setValue("file", FakeUpload("bad.cif.gz", b"this is not gzip data"))
        uu = ServiceUploadUtils(self.__req)
        self.assertIsNone(uu.copyToSession())
        # No partial output left behind
        self.assertFalse(os.path.exists(os.path.join(self.__sessionPath, "bad.cif")))

    def testCopyToSessionGzipTruncated(self) -> None:
        data = gzip.compress(b"x" * 10000)
        self.__req.setValue("file", FakeUpload("short.cif.gz", data[: len(data) // 2]))
        uu = ServiceUploadUtils(self.__req)
        self.assertIsNone(uu.copyToSession())
        self.assertFalse(os.path.exists(os.path.join(self.__sessionPath, "short.cif")))

    def testCopyToSessionGzipNoUncompress(self) -> None:
        self.__req.setValue("file", FakeUpload("model.cif.gz", gzip.compress(b"compressed data")))
        uu = ServiceUploadUtils(self.__req)
        self.assertEqual(uu.copyToSession(uncompress=False), "model.cif.gz")
        self.assertFalse(os.path.exists(os.path.join(self.__sessionPath, "model.cif")))

    def testRenameSessionFile(self) -> None:
        uu = ServiceUploadUtils(self.__req)
        with open(os.path.join(self.__sessionPath, "src.txt"), "w", encoding="utf-8") as ofh:
            ofh.write("content")
        self.assertTrue(uu.renameSessionFile("src.txt", "dst.txt"))
        self.assertTrue(os.path.exists(os.path.join(self.__sessionPath, "dst.txt")))
        # Same name is a no-op
        self.assertTrue(uu.renameSessionFile("src.txt", "src.txt"))
        # Missing source
        self.assertFalse(uu.renameSessionFile("nothere.txt", "dst2.txt"))

    def testGetFileExtension(self) -> None:
        uu = ServiceUploadUtils(self.__req)
        self.assertIsNone(uu.getFileExtension(None))
        self.assertIsNone(uu.getFileExtension(""))
        self.assertIsNone(uu.getFileExtension("noextension"))
        self.assertEqual(uu.getFileExtension("file.cif"), "cif")
        self.assertEqual(uu.getFileExtension("file.cif.V2"), "V2")
        self.assertEqual(uu.getFileExtension("file.cif.V2", ignoreVersion=True), "cif")
        self.assertEqual(uu.getFileExtension("file.cif.v10", ignoreVersion=True), "cif")
        self.assertEqual(uu.getFileExtension("file.cif.gz", ignoreVersion=True), "gz")
        self.assertEqual(uu.getFileExtension("file.cif", ignoreVersion=True), "cif")

    def testPerceiveIdentifier(self) -> None:
        uu = ServiceUploadUtils(self.__req)
        self.assertEqual(uu.perceiveIdentifier(None), (None, None))
        self.assertEqual(uu.perceiveIdentifier(""), (None, None))
        self.assertEqual(uu.perceiveIdentifier("rcsb012345.cif"), ("rcsb012345", "RCSB"))
        self.assertEqual(uu.perceiveIdentifier("D_1000000001_model_P1.cif"), ("D_1000000001", "WF_ARCHIVE"))
        self.assertEqual(uu.perceiveIdentifier("W_000001.cif"), ("W_000001", "WF_INSTANCE"))
        self.assertEqual(uu.perceiveIdentifier("1abc.cif"), ("1abc", "UNKNOWN"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
