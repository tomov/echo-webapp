import base
from base import *
import api_helpers
from api_helpers import *
import mock_data
from mock_data import *

from model import Feedback

class TestMiscAPI(TestBase, MiscAPIHelpers, MockUserData, MockQuoteData, MockCommentData):

    def setUp(self):
        TestBase.setUp(self)
        self.add_user(self.user_simple)

    # ------------- helpers -------------

    # check if db entry feedback after add_feedback(feedback_dict) is same as feedback_dict
    def assert_is_same_feedback(self, feedback, feedback_dict):
        self.assertEqual(feedback.content, feedback_dict['content'])
        self.assertEqual(feedback.version, feedback_dict['version'])

    # ------------- tests -------------

    def test_add_feedback(self):
        feedback_dict = {'content': 'This app sucks cock!!!! I want my money back', 'version': '0.0.0.9'}
        self.add_feedback(feedback_dict, self.user_simple['id'])
        self.assertEqual(Feedback.query.count(), 1) # it's in

        user = User.query.first()
        self.assert_is_same_feedback(user.feedback[0], feedback_dict) # it's correct and added to user


if __name__ == '__main__':
    unittest.main()