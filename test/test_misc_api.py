# -*- coding: utf-8 -*-

import base
from base import *
import api_helpers
from api_helpers import *
import mock_data
from mock_data import *
from model import Feedback, Echo


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

    def test_og_repeater(self):
        tags = {'key': 'value', 'abc': 'def', 'test': 'the og repeater'}
        og_html = self.og_repeater(tags)
        og_html = og_html.replace(' ', '').replace('\t', '')
        expected_html = """<html>
          <head prefix="og: http://ogp.me/ns# fb: http://ogp.me/ns/fb#">
            
            <meta property="test" content="the og repeater" /> 
            
            <meta property="abc" content="def" /> 
            
            <meta property="key" content="value" /> 
            
            <meta property="og:url" content="http://localhost/og_repeater?test=the+og+repeater&amp;abc=def&amp;key=value" />
            <meta http-equiv="refresh" content="0; url='http://echoapp.me/'"> 
          </head>
          <body>
          </body>
        </html>""".replace(' ', '').replace('\t', '')
        self.assertEqual(og_html, expected_html)

    def test_og_quote(self):
        self.add_user(self.user_with_friends)
        self.add_quote(self.quote_minimal)
        echo = Echo.query.first()
        og_html = self.og_quote(echo.id)
        og_html = og_html.replace(' ', '').replace('\t', '')
        expected_html = """<html>
          <head prefix="og: http://ogp.me/ns# fb: http://ogp.me/ns/fb#">
            
            <meta property="og:type" content="echoios:quote" /> 
            
            <meta property="og:description" content="— Elizabeth Greenestein" /> 
            
            <meta property="og:title" content="&#34;Here&#39;s to the crazy ones. The misfits. The rebels. The troublemakers. The round pegs in the square holes.&#34;" /> 
            
            <meta property="og:url" content="http://localhost/og_quote?ref=1" />
            <meta http-equiv="refresh" content="0; url='http://echoapp.me/'"> 
          </head>
          <body>
          </body>
        </html>""".replace(' ', '').replace('\t', '')
        self.assertEqual(og_html, expected_html)


if __name__ == '__main__':
    unittest.main()
