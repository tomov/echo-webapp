# -*- coding: utf-8 -*-

import unittest
from test_user_api import *
from test_quote_api import *
from test_comment_api import *
from test_fav_api import *
from test_echo_api import *
from test_notif_api import *
from test_misc_api import *

def suite():
	test_suite = unittest.TestSuite()
	test_suite.addTest(unittest.makeSuite(TestUserAPI))
	test_suite.addTest(unittest.makeSuite(TestQuoteAPI))
	test_suite.addTest(unittest.makeSuite(TestCommentAPI))
	test_suite.addTest(unittest.makeSuite(TestFavAPI))
	test_suite.addTest(unittest.makeSuite(TestEchoAPI))
	test_suite.addTest(unittest.makeSuite(TestNotifAPI))
	test_suite.addTest(unittest.makeSuite(TestMiscAPI))
	return test_suite

if __name__ == "__main__":
    test_runner = unittest.TextTestRunner()
    test_suite = suite()
    test_runner.run(test_suite)