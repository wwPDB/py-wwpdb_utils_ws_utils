import unittest
from wwpdb.utils.ws_utils.ServiceSessionFactory import ServiceSessionFactory

class ServiceSessionFactoryTests(unittest.TestCase):

    def test_assignid(self):
        ssf = ServiceSessionFactory()
        ret = ssf.getId()
        self.assertIsNone(ret)
        ret = ssf.assignId()
        self.assertIsNotNone(ret)


if __name__ == '__main__':
    unittest.main()
