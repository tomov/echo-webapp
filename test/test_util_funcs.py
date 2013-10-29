import base
from base import *
from util import *
from model import Feedback


class TestUtilFuncs(TestBase):

    def setUp(self):
        TestBase.setUp(self)

    # ------------- tests -------------

    def test_split_name(self):
        first, last = split_name("");
        self.assertEqual(first, "")
        self.assertEqual(last, "")

        first, last = split_name("Momchil");
        self.assertEqual(first, "Momchil")
        self.assertEqual(last, "")

        first, last = split_name("Momchil Tomov");
        self.assertEqual(first, "Momchil")
        self.assertEqual(last, "Tomov")

        first, last = split_name("Emmiliese von Clemm");
        self.assertEqual(first, "Emmiliese")
        self.assertEqual(last, "von Clemm")

        first, last = split_name("Joan Bosco Albanell Flores");
        self.assertEqual(first, "Joan")
        self.assertEqual(last, "Bosco Albanell Flores")


if __name__ == '__main__':
    unittest.main()