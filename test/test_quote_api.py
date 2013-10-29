import base
from base import *
import api_helpers
from api_helpers import *
import mock_data
from mock_data import *

from model import Favorite, Echo, Comment

class TestQuoteAPI(TestBase, QuoteAPIHelpers, MockUserData, MockQuoteData):

    def setUp(self):
        TestBase.setUp(self)
        self.add_user(self.user_simple)
        self.add_user(self.user_with_friends)
        self.add_user(self.user_unicode_simple)
        self.add_user(self.user_passive_spectator)

    # ------------- helpers -------------

    # check if the db entry quote after add_quote(quote_dict) is consistent with quote_dict
    def assert_is_same_quote_simple(self, quote, quote_dict, deleted = False):
        self.assertIsNotNone(quote)
        self.assertEqual(quote.deleted, deleted)
        self.assertEqual(quote.content, quote_dict['quote'].decode('utf8'))

        source = User.query.filter_by(fbid = quote_dict['sourceFbid']).first()
        self.assertIsNotNone(source)
        self.assertEqual(quote.source_id, source.id)

        reporter = User.query.filter_by(fbid = quote_dict['reporterFbid']).first()
        self.assertIsNotNone(reporter)
        self.assertEqual(quote.reporter_id, reporter.id)

        if 'location' in quote_dict:
            self.assertEqual(quote.location, quote_dict['location'])
        if 'location_lat' in quote_dict:
            self.assertEqual(quote.location_lat, quote_dict['location_lat'])
        if 'location_long' in quote_dict:
            self.assertEqual(quote.location_long, quote_dict['location_long'])

    # check if quote_res = get_quote(...) is consistent with db entry quote
    # note this only works with original quotes, not with echoes
    def assert_is_consistent_quote_simple(self, quote_res, user_fbid):
        quote = Quote.query.filter_by(id=quote_res['_id']).first()
        self.assertIsNotNone(quote)
        self.assertFalse(quote.deleted)

        self.assertEqual(quote.content, quote_res['quote'])
        self.assertEqual(quote.location, quote_res['location'])
        self.assertEqual(quote.location_lat, quote_res['location_lat'])
        self.assertEqual(quote.location_long, quote_res['location_long'])

        self.assertIsNotNone(quote.source)
        self.assertEqual(quote.source.fbid, quote_res['sourceFbid'])
        self.assertEqual(quote.source.first_name + " " + quote.source.last_name, quote_res['source_name'])
        self.assertEqual(quote.source.picture_url, quote_res['source_picture_url'])

        self.assertIsNotNone(quote.reporter)
        self.assertEqual(quote.reporter.fbid, quote_res['reporterFbid'])
        self.assertEqual(quote.reporter.first_name + " " + quote.reporter.last_name, quote_res['reporter_name'])
        self.assertEqual(quote.reporter.picture_url, quote_res['reporter_picture_url'])

        self.assertIn('timestamp', quote_res)
        self.assertEqual(len(quote.echoers) - 1, quote_res['echo_count'])
        self.assertEqual(len(quote.favs), quote_res['fav_count'])

        user = User.query.filter_by(fbid=user_fbid).first()
        self.assertEqual(Favorite.query.filter_by(quote_id=quote.id, user_id=user.id).count() > 0, quote_res['user_did_fav'])
        self.assertEqual(user.id != quote.reporter_id and Echo.query.filter_by(quote_id=quote.id, user_id=user.id).count() > 0, quote_res['user_did_echo'])

        self.assertFalse(quote_res['is_echo'])
        echo = Echo.query.filter(Echo.quote_id==quote.id, Echo.user_id==quote.reporter_id).first()
        self.assertIsNotNone(echo)
        self.assertEqual(echo.id, quote_res['order_id'])

    # same as above but also compares comments
    def assert_is_consistent_quote_with_comments(self, quote_res, user_fbid):
        self.assert_is_consistent_quote_simple(quote_res, user_fbid)
        
        quote = Quote.query.filter_by(id=quote_res['_id']).first()
        user = User.query.filter_by(fbid=user_fbid).first()
        ids = [friend.id for friend in user.all_friends] + [user.id]
        comments_dicts = []
        for comment in quote.comments:
            comment_dict = {
                "id": comment.id,
                "fbid": comment.user.fbid,
                "timestamp": datetime_to_timestamp(comment.created),
                "comment": comment.content,
                "name": comment.user.first_name + ' ' + comment.user.last_name,
                "picture_url": comment.user.picture_url,
                "is_friend_or_me": comment.user_id in ids
            }
            comments_dicts.append(comment_dict)
        self.assertItemsEqual(comments_dicts, quote_res['comments'])

    # same as above but for multiple quotes, i.e. quotes_res = get_quotes(...)
    # where before that we called add_quote(quotes_dicts[i]) for all i
    # and we're expecting to receive quotes_dicts[j] for all j in indices
    def assert_are_consistent_quotes(self, quotes_res, indices, user_fbid):
        self.assertEqual(len(quotes_res), len(indices)) # got 'em all
        for i in range(len(indices)):
            self.assertEqual(quotes_res[i]['_id'], str(indices[i])) # the correct quotes in the correct order
            self.assert_is_consistent_quote_simple(quotes_res[i], self.user_simple['id']) # with the right data

    # ------------- tests -------------

    def test_add_quote(self):
        rv = self.add_quote(self.quote_minimal)
        # TODO test if response is {echo_id: 1}
        self.assertEqual(Quote.query.count(), 1) # quote added

        quote = Quote.query.first()
        self.assert_is_same_quote_simple(quote, self.quote_minimal) # quote is fine

        self.add_quote(self.quote_normal)
        self.assertEqual(Quote.query.count(), 2) # quote added

        quote = Quote.query.all()[1]
        self.assert_is_same_quote_simple(quote, self.quote_normal) # quote is fine


    def test_add_quote_unicode(self):
        # TODO broken
        self.add_quote(self.quote_unicode)
        self.assertEqual(Quote.query.count(), 1) # quote added

        quote = Quote.query.first()
        print quote.content
        self.assert_is_same_quote_simple(quote, self.quote_unicode) # quote is fine

    def test_add_quote_invalid(self):
        self.add_quote(self.quote_invalid_source)
        self.assertEqual(Quote.query.count(), 0) # invalid source

        self.add_quote(self.quote_invalid_reporter, self.user_simple['id'])
        self.assertEqual(Quote.query.count(), 0) # invalid reporter

        self.add_quote(self.quote_same_source_reporter)
        self.assertEqual(Quote.query.count(), 0) # source = reporter

    def test_delete_quote(self):
        self.add_quote(self.quote_minimal)
        self.delete_quote("1", self.quote_minimal['reporterFbid'])
        self.assertEqual(Quote.query.count(), 1) # do not remove from db
        quote = Quote.query.first()
        self.assert_is_same_quote_simple(quote, self.quote_minimal, True) # deleted by reporter

        self.add_quote(self.quote_minimal)
        self.delete_quote("2", self.quote_minimal['sourceFbid'])
        quote = Quote.query.all()[1]
        self.assert_is_same_quote_simple(quote, self.quote_minimal, True) # deleted by source

    def test_delete_quote_invalid(self):
        self.add_quote(self.quote_minimal)

        self.delete_quote("1", "invalid")
        quote = Quote.query.first()
        self.assert_is_same_quote_simple(quote, self.quote_minimal) # not deleted -- invalid user

        self.delete_quote("1", self.user_unicode_simple['id'])
        quote = Quote.query.first()
        self.assert_is_same_quote_simple(quote, self.quote_minimal) # not deleted -- user is not reporter nor source

        self.delete_quote("2", self.quote_minimal['reporterFbid'])
        quote = Quote.query.first()
        self.assert_is_same_quote_simple(quote, self.quote_minimal) # not deleted -- wrong quote id

    def test_get_quote_simple(self):
        self.assertTrue(self.add_quote_to_db(self.quote_minimal))
        quote_res = self.get_quote("1", self.user_simple['id'])
        self.assert_is_consistent_quote_simple(quote_res, self.user_simple['id'])

    def test_get_quote_with_comments(self):
        self.assertTrue(self.add_quote_to_db(self.quote_minimal))
        db.session.add(Comment(1, 1, "Example quote by the first user")) # HARDCODED user id's
        db.session.add(Comment(2, 1, "Another example quote, this time by the second user"))
        quote_res = self.get_quote("1", self.user_simple['id'])
        self.assert_is_consistent_quote_with_comments(quote_res, self.user_simple['id'])

    def test_get_quote_unicode(self):
        self.assertTrue(self.add_quote_to_db(self.quote_unicode))
        quote_res = self.get_quote("1", self.user_simple['id'])
        self.assert_is_consistent_quote_simple(quote_res, self.user_simple['id'])

    def test_get_quote_invalid(self):
        self.assertTrue(self.add_quote_to_db(self.quote_minimal))

        quote_res = self.get_quote("2", self.user_simple['id'])
        self.assertIn('error', quote_res) # echo with given id doesn't exist

        quote_res = self.get_quote("1", "invalid")
        self.assertIn('error', quote_res) # invalid user

        quote = Quote.query.first()
        quote.deleted = True
        db.session.commit()
        quote_res = self.get_quote("1", self.user_simple['id'])
        self.assertIn('error', quote_res) # corresponding quote was marked as deleted

        quote = Quote.query.first()
        db.session.delete(quote)
        db.session.commit()
        quote_res = self.get_quote("1", self.user_simple['id'])
        self.assertIn('error', quote_res) # corresponding quote doesn't exist

    def test_check_deleted_quotes(self):
        self.assertTrue(self.add_quote_to_db(self.quote_minimal))
        self.assertTrue(self.add_quote_to_db(self.quote_minimal))
        quote = Quote.query.all()[1]
        db.session.delete(quote)
        quote = Quote.query.all()[1]
        quote.deleted = True
        db.session.commit()

        is_deleted = self.check_deleted_quotes([1, 2, 3, 4], self.user_simple['id'])
        self.assertItemsEqual(is_deleted, [{'order_id': 1}, None, None, None])

    def test_get_quotes_simple(self):
        quotes_dicts = [self.quote_minimal, self.quote_normal, self.quote_normal_two]
        for i in range(3):
            self.assertTrue(self.add_quote_to_db(quotes_dicts[i]))
        quotes_res = self.get_quotes(self.user_simple['id'], 10)
        self.assert_are_consistent_quotes(quotes_res, [3, 2, 1], self.user_simple['id'])

    def test_get_quotes_with_params(self):
        quotes_dicts = [self.quote_minimal, self.quote_normal, self.quote_normal_two, self.quote_minimal_flipped]
        for i in range(4):
            self.assertTrue(self.add_quote_to_db(quotes_dicts[i]))

        quotes_res = self.get_quotes(self.user_simple['id'], 10)
        self.assert_are_consistent_quotes(quotes_res, [4, 3, 2, 1], self.user_simple['id']) # no params

        quotes_res = self.get_quotes(self.user_simple['id'], 1)
        self.assert_are_consistent_quotes(quotes_res, [4], self.user_simple['id']) # limit

        quotes_res = self.get_quotes(self.user_simple['id'], 10, 1)
        self.assert_are_consistent_quotes(quotes_res, [4, 3, 2], self.user_simple['id']) # latest

        quotes_res = self.get_quotes(self.user_simple['id'], 2, 1)
        self.assert_are_consistent_quotes(quotes_res, [4, 3], self.user_simple['id']) # latest & limit

        quotes_res = self.get_quotes(self.user_simple['id'], 10, None, 3)
        self.assert_are_consistent_quotes(quotes_res, [2, 1], self.user_simple['id']) # oldest

        quotes_res = self.get_quotes(self.user_simple['id'], 2, None, 4)
        self.assert_are_consistent_quotes(quotes_res, [3, 2], self.user_simple['id']) # oldest & limit

        quotes_res = self.get_quotes(self.user_simple['id'], 10, 2, 2)
        self.assert_are_consistent_quotes(quotes_res, [2], self.user_simple['id']) # latest & oldest

        quotes_res = self.get_quotes(self.user_simple['id'], 10, 3, 1)
        self.assert_are_consistent_quotes(quotes_res, [3, 2, 1], self.user_simple['id']) # latest & oldest again

        quotes_res = self.get_quotes(self.user_simple['id'], 10, 1, 3)
        self.assert_are_consistent_quotes(quotes_res, [3, 2, 1], self.user_simple['id']) # oldest & latest flipped

        quotes_res = self.get_quotes(self.user_simple['id'], 10, 4, 2)
        self.assert_are_consistent_quotes(quotes_res, [4, 3, 2], self.user_simple['id']) # latest & oldest again

        quotes_res = self.get_quotes(self.user_simple['id'], 10, 4, 1)
        self.assert_are_consistent_quotes(quotes_res, [4, 3, 2, 1], self.user_simple['id']) # latest & oldest again

        quotes_res = self.get_quotes(self.user_simple['id'], 1, 3, 1)
        self.assert_are_consistent_quotes(quotes_res, [3], self.user_simple['id']) # latest & oldest & limit

        quotes_res = self.get_quotes(self.user_simple['id'], 2, 3, 1)
        self.assert_are_consistent_quotes(quotes_res, [3, 2], self.user_simple['id']) # latest & oldest & limit again

        quotes_res = self.get_quotes(self.user_simple['id'], 3, 3, 1)
        self.assert_are_consistent_quotes(quotes_res, [3, 2, 1], self.user_simple['id']) # latest & oldest & limit again

        quotes_res = self.get_quotes(self.user_simple['id'], 10, None, None, self.user_simple['id'])
        self.assert_are_consistent_quotes(quotes_res, [4, 2, 1], self.user_simple['id']) # profile_fbid

        quotes_res = self.get_quotes(self.user_simple['id'], 10, None, None, self.user_with_friends['id'])
        self.assert_are_consistent_quotes(quotes_res, [4, 3, 2, 1], self.user_simple['id']) # profile_fbid with other user

        quotes_res = self.get_quotes(self.user_simple['id'], 10, None, None, self.user_passive_spectator['id'])
        self.assert_are_consistent_quotes(quotes_res, [3], self.user_simple['id']) # profile_fbid with another user

        quotes_res = self.get_quotes(self.user_simple['id'], 10, 1, None, self.user_simple['id'])
        self.assert_are_consistent_quotes(quotes_res, [4, 2], self.user_simple['id']) # profile_fbid, latest

        quotes_res = self.get_quotes(self.user_simple['id'], 10, None, 4, self.user_simple['id'])
        self.assert_are_consistent_quotes(quotes_res, [2, 1], self.user_simple['id']) # profile_fbid, oldest

        quotes_res = self.get_quotes(self.user_simple['id'], 10, 3, 2, self.user_simple['id'])
        self.assert_are_consistent_quotes(quotes_res, [2], self.user_simple['id']) # profile_fbid, latest & oldest

        quotes_res = self.get_quotes(self.user_simple['id'], 10, 4, 2, self.user_simple['id'])
        self.assert_are_consistent_quotes(quotes_res, [4, 2], self.user_simple['id']) # profile_fbid, latest & oldest again

        quotes_res = self.get_quotes(self.user_simple['id'], 10, 3, 1, self.user_simple['id'])
        self.assert_are_consistent_quotes(quotes_res, [2, 1], self.user_simple['id']) # profile_fbid, latest & oldest again

        quotes_res = self.get_quotes(self.user_simple['id'], 1, 3, 1, self.user_simple['id'])
        self.assert_are_consistent_quotes(quotes_res, [2], self.user_simple['id']) # profile_fbid, latest & oldest & limit

    def UNDONE_test_get_quotes_with_echoes(self):
        # TODO
        pass

    def test_get_quotes_deleted(self):
        quotes_dicts = [self.quote_minimal, self.quote_normal, self.quote_normal_two, self.quote_minimal_flipped]
        self.assertTrue(self.add_quote_to_db(quotes_dicts[0]))
        self.assertTrue(self.add_quote_to_db(quotes_dicts[1], True))
        self.assertTrue(self.add_quote_to_db(quotes_dicts[2], True))
        self.assertTrue(self.add_quote_to_db(quotes_dicts[3]))

        quotes_res = self.get_quotes(self.user_simple['id'], 10)
        self.assert_are_consistent_quotes(quotes_res, [4, 1], self.user_simple['id'])

        quote = Quote.query.all()[3]
        quote.deleted = True
        db.session.commit()
        quotes_res = self.get_quotes(self.user_simple['id'], 10)
        self.assert_are_consistent_quotes(quotes_res, [1], self.user_simple['id'])


    def test_get_quotes_unicode(self):
        quotes_dicts = [self.quote_minimal, self.quote_unicode, self.quote_unicode_flipped]
        for i in range(3):
            self.assertTrue(self.add_quote_to_db(quotes_dicts[i]))

        quotes_res = self.get_quotes(self.user_simple['id'], 10)
        self.assert_are_consistent_quotes(quotes_res, [3, 2, 1], self.user_simple['id'])

        quotes_res = self.get_quotes(self.user_simple['id'], 10, None, None, self.user_simple['id'])
        self.assert_are_consistent_quotes(quotes_res, [1], self.user_simple['id']) # profile_fbid

        quotes_res = self.get_quotes(self.user_simple['id'], 10, None, None, self.user_with_friends['id'])
        self.assert_are_consistent_quotes(quotes_res, [3, 2, 1], self.user_simple['id']) # profile_fbid

        quotes_res = self.get_quotes(self.user_simple['id'], 10, None, None, self.user_unicode_simple['id'])
        self.assert_are_consistent_quotes(quotes_res, [3, 2], self.user_simple['id']) # profile_fbid & unicode user

    def test_get_quotes_invalid(self):
        quotes_dicts = [self.quote_minimal, self.quote_normal, self.quote_normal_two]
        for i in range(3):
            self.assertTrue(self.add_quote_to_db(quotes_dicts[i]))

        quotes_res = self.get_quotes("invalid", 10)
        self.assertIn('error', quotes_res) # invalid user

        quotes_res = self.get_quotes(self.user_simple['id'], 10, None, None, "invalid")
        self.assertIn('error', quotes_res) # invalid profile user

        quotes_res = self.get_quotes(self.user_simple['id'], "")
        self.assertIn('error', quotes_res) # no limit


if __name__ == '__main__':
    unittest.main()