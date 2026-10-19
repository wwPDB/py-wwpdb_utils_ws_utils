import os
import tempfile
import unittest

from wwpdb.utils.ws_utils.ServiceSessionFactory import ServiceSessionFactory


class ServiceSessionFactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpdir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.__topPath = self.__tmpdir.name

    def tearDown(self) -> None:
        self.__tmpdir.cleanup()

    def test_assignid(self) -> None:
        ssf = ServiceSessionFactory()
        ret = ssf.getId()
        self.assertIsNone(ret)
        ret = ssf.assignId()
        self.assertIsNotNone(ret)
        self.assertEqual(ssf.getId(), ret)

    def test_defaults(self) -> None:
        ssf = ServiceSessionFactory()
        self.assertEqual(ssf.getTopPath(), ".")
        self.assertEqual(ssf.getTopSessionPath(), ".")
        self.assertEqual(ssf.getSessionUserPath(), os.path.join(".", "sessions", "ANONYMOUS"))
        # No id assigned - no path
        self.assertIsNone(ssf.getPath())
        self.assertIsNone(ssf.getRelativePath())
        self.assertIsNone(ssf.makeSessionPath())
        self.assertIsNone(ssf.remakeSessionPath())

    def test_setters(self) -> None:
        ssf = ServiceSessionFactory()
        self.assertTrue(ssf.setTopPath(self.__topPath))
        self.assertEqual(ssf.getTopPath(), self.__topPath)
        self.assertTrue(ssf.setTopSessionPath("/other"))
        self.assertEqual(ssf.getTopSessionPath(), "/other")
        self.assertTrue(ssf.setServiceUserId("user1"))
        self.assertEqual(ssf.getSessionUserPath(), os.path.join("/other", "sessions", "user1"))
        self.assertTrue(ssf.setId("abc"))
        self.assertEqual(ssf.getId(), "abc")
        self.assertEqual(ssf.getRelativePath(), os.path.join("/sessions", "user1", "abc"))

    def test_session_paths(self) -> None:
        ssf = ServiceSessionFactory(topPath=self.__topPath, serviceUserId="user1")
        uid = ssf.assignId()
        expected = os.path.join(self.__topPath, "sessions", "user1", uid)

        # Path not yet created
        self.assertIsNone(ssf.getPath())

        self.assertEqual(ssf.makeSessionPath(), expected)
        self.assertTrue(os.path.isdir(expected))
        self.assertEqual(ssf.getPath(), expected)
        # Already exists
        self.assertEqual(ssf.makeSessionPath(), expected)

        # remake removes existing contents
        tfile = os.path.join(expected, "afile.txt")
        with open(tfile, "w", encoding="utf-8") as ofh:
            ofh.write("data")
        self.assertEqual(ssf.remakeSessionPath(), expected)
        self.assertTrue(os.path.isdir(expected))
        self.assertFalse(os.path.exists(tfile))

        s = str(ssf)
        self.assertIn(uid, s)
        self.assertIn("user1", s)
        self.assertEqual(repr(ssf), s)


if __name__ == "__main__":
    unittest.main()
