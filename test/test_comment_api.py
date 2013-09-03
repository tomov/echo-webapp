import base
from base import *
import api_helpers
from api_helpers import *
import mock_data
from mock_data import *

from model import Comment

class TestCommentAPI(TestBase, CommentAPIHelpers, MockUserData, MockQuoteData, MockCommentData):

    def setUp(self):
        TestBase.setUp(self)
        self.add_user(self.user_simple)
        self.add_user(self.user_with_friends)
        self.add_user(self.user_unicode_simple)
        self.add_quote(self.quote_minimal)
        self.add_quote(self.quote_normal)

    # ------------- helpers -------------

    def assert_is_same_comment(self, comment, comment_dict):
        self.assertIsNotNone(comment)
        self.assertEqual(comment.user.fbid, comment_dict['userFbid'])
        self.assertEqual(comment.content, comment_dict['comment'].decode('utf8'))
        self.assertEqual(str(comment.quote_id), comment_dict['quoteId'])

    # ------------- tests -------------

    def test_add_comment(self):
        self.add_comment(self.comment_for_quote_one)
        self.assertEqual(Comment.query.count(), 1) # comment added

        comment = Comment.query.first()
        self.assert_is_same_comment(comment, self.comment_for_quote_one) # comment is fine

        quote = Quote.query.first()
        self.assertEqual(Comment.query.filter_by(quote_id=1).count(), 1) # and in quote
        self.assert_is_same_comment(quote.comments[0], self.comment_for_quote_one) # and is fine there too

        self.add_comment(self.comment_for_quote_one_again)
        self.assertEqual(Comment.query.count(), 2) # second comment added
        self.assertEqual(Comment.query.filter_by(quote_id=1).count(), 2) # and in quote

        quote = Quote.query.first()
        self.assert_is_same_comment(quote.comments[1], self.comment_for_quote_one_again) # and is fine too

        self.add_comment(self.comment_for_quote_two)
        quote = Quote.query.all()[1]
        self.assertEqual(Comment.query.filter_by(quote_id=2).count(), 1) # added to second quote
        self.assert_is_same_comment(quote.comments[0], self.comment_for_quote_two) # and is fine

    def BROKEN_test_add_comment_unicode(self):
        # TODO broken
        self.add_comment(self.comment_unicode)
        self.assertEqual(Comment.query.count(), 1) # comment added

        comment = Comment.query.first()
        self.assert_is_same_comment(comment, self.comment_unicode) # comment is fine

    def test_add_comment_invalid(self):
        self.add_comment(self.comment_for_quote_one, "invalid")
        self.assertEqual(Comment.query.count(), 0) # invalid user

        self.add_comment(self.comment_invalid_quote)
        self.assertEqual(Comment.query.count(), 0) # invalid quote

        quote = Quote.query.first()
        quote.deleted = True
        db.session.commit()
        self.add_comment(self.comment_for_quote_one)
        self.assertEqual(Comment.query.count(), 0) # quote deleted

    def test_delete_comment(self):
        self.add_comment(self.comment_for_quote_one)
        self.delete_comment("1", self.user_simple['id'])
        self.assertEqual(Comment.query.count(), 0) # deleted

    def test_delete_invalid(self):
        self.add_comment(self.comment_for_quote_one)

        self.delete_comment("1", "invalid")
        comment = Comment.query.first()
        self.assert_is_same_comment(comment, self.comment_for_quote_one) # not deleted -- invalid user

        self.delete_comment("2", self.user_simple['id'])
        comment = Comment.query.first()
        self.assert_is_same_comment(comment, self.comment_for_quote_one) # not deleted -- invalid comment_id


if __name__ == '__main__':
    unittest.main()