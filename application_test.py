# -*- coding: utf-8 -*-

import os
import unittest
import tempfile
import json
from sqlalchemy import desc
from flask.ext.sqlalchemy import SQLAlchemy
from pprint import pprint
import time
from copy import copy

import application
import model
from model import db
from model import User, Quote, Comment, Favorite, Echo, Notification, NotifPrefs, Feedback
from constants import *
from test_data import *
from util import *

# DO NOT TOUCH THIS!!!!! If you do, you might fuck up the real db, and Momchil will personally come find you and behead you in your sleep
TEST_DATABASE_NAME = 'echo_webapp_test'
TEST_DATABASE_URI = DatabaseConstants.DATABASE_LOCAL_URI_TEMPLATE % TEST_DATABASE_NAME # DO NOT FUCK THIS UP! or you'll erase the real db....

#: these lines will be used throughout for debugging purposes
print '===> _before: using db -- ' + application.app.config['SQLALCHEMY_DATABASE_URI']

class TestBase(unittest.TestCase):

    def setUp(self): #: called before each individual test function is run
        application.app.config['SQLALCHEMY_DATABASE_URI'] = TEST_DATABASE_URI
        print '\n===> setup: using db -- ' + application.app.config['SQLALCHEMY_DATABASE_URI']

        db.app = application.app
        self.app = application.app.test_client()
        db.create_all() #: initialize all tables

    def tearDown(self): #: called after the test is run (close shit)
        db.session.remove() # REALLY IMPORTANT to do this before the one below, otherwise can't run more than one test
        db.drop_all() #: get rid of tables
        print '===> teardown: end'


# Note these are real Facebook test users for Echo that can be edited here:
# https://developers.facebook.com/apps/193862260739040/roles?role=test%20users
class MockUserData():

    user_simple = {
        "id": "100006629105407",
        "email": "khrfkvs_wisemanescu_1378106137@tfbnw.net",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc7/370214_100000486204833_1328204472_q.jpg",
        "name": "Helen Wisemanescu", 
        "friends": [],
        "unfriends": []
    }

    user_with_friends = {
        "id": "100006546972451",
        "email": "gwncgzh_greenestein_1378106136@tfbnw.net",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc6/274340_1778127543_1201810974_q.jpg",
        "name": "Elizabeth Greenestein", 
        "friends": [
            {
                "id": user_simple['id'],
                "name": user_simple['name'],
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/203434_703951380_2070708925_q.jpg"
                    }
                }, 
            },
            {
                "id": "1778127543", 
                "name": "Michele Alex",
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/370322_100002571158857_1251482889_q.jpg"
                    }
                }, 
            },
            {
                "id": "100001040617130", 
                "name": "Momchil's Mom",
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc6/275685_100001040617130_24180076_q.jpg"
                    }
                }, 
            },
        ],
        "unfriends": []
    }

    # see HARDCODED below if you change this guy
    user_with_friends_update = {
        "id": user_with_friends['id'],
        "email": "new_email@gmail.com",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc6/274340_1778127543_1201810974666666.jpg",
        "name": user_with_friends['name'],
        "friends": [
            {
                "id": user_simple['id'],
                "name": user_simple['name'],
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/203434_703951380_2070708925_q.jpg"
                    }
                }, 
            },
            {
                "id": "11324123412341234", 
                "name": "Somebody New",
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/203434_703951380_20707089251111_q.jpg"
                    }
                }, 
            }
        ],
        "unfriends": [user_with_friends['friends'][1]['id'], user_with_friends['friends'][2]['id'], "invalid"]
    }

    user_unicode_simple = {
        "id": "100006688621903",
        "email": "mknoabj_mcdonaldsen_1378106135@tfbnw.net",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc7/370214_100000486204833_1328204472_qq123.jpg",
        "name": "Дейв МакДоналдсън",
        "friends": [],
        "unfriends": []
    }

    user_invalid_fbid = {
        "id": "invalid",
        "email": "khrfkvs_wisemanescu_1378106137@tfbnw.net",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc7/370214_100000486204833_1328204472_q.jpg",
        "name": "Helen Wisemanescu", 
        "friends": [],
        "unfriends": []
    }

    user_passive_spectator = {
        "id": "100006678452194",
        "email": "random@gmail.com",
        "picture_url": "https://there-is-no-such-url/1328204472_q.jpg",
        "name": "Donna Shepardwitz", 
        "friends": [],
        "unfriends": []
    }

    user_passive_spectator_with_friends = {
        "id": user_passive_spectator['id'],
        "email": user_passive_spectator['email'],
        "picture_url": user_passive_spectator['picture_url'],
        "name": user_passive_spectator['name'],
        "friends": [
            {
                "id": user_simple['id'],
                "name": user_simple['name'],
                "picture": { 
                    "data": {
                        "url": user_simple['picture_url']
                    }
                }, 
            },
            {
                "id": user_with_friends['id'],
                "name": user_with_friends['name'],
                "picture": { 
                    "data": {
                        "url": user_with_friends['picture_url']
                    }
                }, 
            }
        ],
        "unfriends": []
    }

    # these should be periodically updated from 
    # https://developers.facebook.com/apps/193862260739040/roles?role=test%20users
    fbids_tokens = {
        "100006678452194": "CAACwURMvyZBABAFMggOKCgKIc1wQiuBhaWHvedkY9u2od1ukTBTSnYDR72Tlg7au0ZAPWMGSUhDjpgCF2u2zmLX6CHBVGhZC2l5Nxy9uBKtqgWKmWGyNItyDrmB2oLZCljIXllZARSeIwcgfctV9WqeYb43WNmvWXhgUHFipKUrbtECLCRl2X2dSKbvT01JgZD",
        "100006629105407": "CAACwURMvyZBABAIh4hEergXqYhp9jV9SZCxrwSVyVZAxo1431xLATMLYYW0sTOtHXWzhyHoZCcBsHQUV8rCa8444YnrbJcwqAkxowaFS69rTJXFZAwZCF1cwcWep1545J0usThTiSgCVB6moPJVGBmvjyFf8yTMzJPGHMgGCPnFbDiaAxUjycypcKTOa1X5S8ZD",
        "100006546972451": "CAACwURMvyZBABAAK5ljWfvBp1tlgRZAdzRvWra9wdseK5joCiwUuKjRvC7tlBKKrMa1ZCbTETdaTFBtyiY2azmFPbroHkK3303qHhX2mwJzVufhdWEl52ZAZAvGgLsF48Pts4m1B84sR8jVDtXSGGcsvaHoAh80lYoJ5yeMM4rdP2zt5KNcIm6EFtDCGMGK4ZD",
        "100006688621903": "CAACwURMvyZBABAJHI8uPXAp8xSLCOoAJ3hZBqw0XQkFJtMYT78Jvzovzu8ZB8w0eTy5AJNMOivLMM0VWiHNgnrcCa7Dzz1lYjDTyCsC1CRECSuUCmpQZAaIY3l7Us8KsKZBUhZBaWWeCGnE9WZCPjN2lTGQnwbO6Rwg5LJjdAZAYerYdrHiSpN6P7QRwnbsOwZBMZD",
    }

class UserAPIHelpers():

    def get_token_for_user_with_fbid(self, user_fbid):
        rv = self.app.get('/get_token?fbid=%s&token=%s' % (user_fbid, MockUserData.fbids_tokens.get(user_fbid)))
        rv = json.loads(rv.data)
        return rv.get('access_token');

    def add_user(self, user_dict):
        token = self.get_token_for_user_with_fbid(user_dict['id'])
        self.app.post('/add_user?token=%s' % token, data=dict(data=json.dumps(user_dict)))


class TestUserAPI(TestBase, UserAPIHelpers, MockUserData):

    # ------------- helpers -------------

    # check if db entry user after add_user(user_dict) is the same as user_dict
    def assert_is_same_user_simple(self, user, user_dict):
        self.assertIsNotNone(user)
        self.assertTrue(user.registered)
        self.assertEqual(user.email, user_dict['email'].decode('utf-8'))
        self.assertEqual(user.picture_url, user_dict['picture_url'])
        self.assertEqual(user.fbid, user_dict['id'])
        first, last = split_name(user_dict['name'].decode('utf-8'))
        self.assertEqual(user.first_name, first.decode('utf-8'))
        self.assertEqual(user.last_name, last.decode('utf-8'))
        self.assertEqual(len(user.all_friends), len(user_dict['friends']))

    # same as above but also checks for friends
    def assert_is_same_user_with_friends(self, user, user_dict):
        self.assert_is_same_user_simple(user, user_dict)
        all_friends_dicts = []
        for friend in user.all_friends:
            friend_dict = {
                "id": friend.fbid,
                "name": friend.first_name + " " + friend.last_name,
                "picture": {
                    "data": {
                        "url": friend.picture_url
                    }
                }
            }
            all_friends_dicts.append(friend_dict)
        self.assertItemsEqual(all_friends_dicts, user_dict['friends'])

    # make sure every friend of user also has user as a friend
    def assert_friends_reciprocity(self, user):
        self.assertIsNotNone(user)
        for friend in user.all_friends:
            self.assertTrue(user in friend.all_friends)

    # ------------- tests -------------

    def testget_token(self):
        token = self.get_token_for_user_with_fbid(self.user_simple['id'])
        self.assertEqual(User.query.count(), 1) # hollow profile is created

    def test_get_token_invalid(self):
        token = self.get_token_for_user_with_fbid("invalid")
        self.assertEqual(User.query.count(), 0) # no hollow profile is created

    def test_add_user_simple(self):
        self.add_user(self.user_simple)
        self.assertEqual(User.query.count(), 1) # user info is updated (no new user is created)

        user = User.query.first()
        self.assert_is_same_user_simple(user, self.user_simple)

    def test_add_user_simple_invalid(self):
        self.add_user(self.user_invalid_fbid)
        self.assertEqual(User.query.count(), 0) # no user is created

    def test_add_user_with_friends(self):
        self.add_user(self.user_with_friends)
        self.assertEqual(User.query.count(), 1 + len(self.user_with_friends['friends'])) # friends are added as users

        user = User.query.first()
        self.assert_is_same_user_with_friends(user, self.user_with_friends) # user and friend data is ok
        self.assert_friends_reciprocity(user) # friend relationships are symmetrical

    def test_add_user_with_friends_extended(self):
        self.add_user(self.user_simple)
        self.add_user(self.user_with_friends)
        self.assertEqual(User.query.count(), 1 + len(self.user_with_friends['friends'])) # existing friend is not duplicated

        user = User.query.filter_by(fbid=self.user_with_friends['id']).first()
        self.assert_is_same_user_with_friends(user, self.user_with_friends) # existing friend picture_url is updated
        self.assert_friends_reciprocity(user) # existing friend knows about new user

        self.add_user(self.user_with_friends_update)
        self.assertEqual(User.query.count(), 1 + len(self.user_with_friends['friends']) + 1) # HARDCODED + 1 user -- one new friend and new user

        user = User.query.filter_by(fbid=self.user_with_friends_update['id']).first()
        self.assert_is_same_user_with_friends(user, self.user_with_friends_update) # friends and data is updated. Notice one friend is duplicate and one unfriend is non-existing
        self.assert_friends_reciprocity(user) # new relationship is symmetrical

        for user in User.query.all(): # unfriends are unfriended and it's symmetrical, also HARDCODED
            if user.fbid != self.user_with_friends_update['id']:
                if user.fbid in self.user_with_friends_update['unfriends']:
                    self.assertEqual(len(user.all_friends), 0)
                else:
                    self.assertEqual(len(user.all_friends), 1)

    def test_add_user_unicode(self):
        self.add_user(self.user_unicode_simple)
        self.assertEqual(User.query.count(), 1) # user added

        user = User.query.first()
        self.assert_is_same_user_simple(user, self.user_unicode_simple)


class MockQuoteData():

    quote_minimal = {
        "quote": "Here's to the crazy ones. The misfits. The rebels. The troublemakers. The round pegs in the square holes.",
        "reporterFbid": MockUserData.user_simple['id'],
        "sourceFbid": MockUserData.user_with_friends['id']
    }

    quote_minimal_flipped = {
        "quote": "Here's to the round pegs in the square holes. The troublemakers. The rebels. The misfits. The crazy ones.",
        "reporterFbid": MockUserData.user_with_friends['id'],
        "sourceFbid": MockUserData.user_simple['id']
    }

    quote_normal = {
        "location": "Randomtown, USA",
        "location_lat": 2343.34352,
        "location_long": 34642.45,
        "quote": "This is a sample quote with no particular entertainment value.",
        "reporterFbid": MockUserData.user_simple['id'],
        "sourceFbid": MockUserData.user_with_friends['id']
    }

    quote_unicode = {
        "quote": "От една страна си ебало майката, от друга страна майката си ебало!!!",
        "reporterFbid": MockUserData.user_with_friends['id'],
        "sourceFbid": MockUserData.user_unicode_simple['id']
    }

    quote_unicode_flipped = {
        "quote": "От една страна майката си ебало, от друга страна си ебало майката!!!",
        "reporterFbid": MockUserData.user_unicode_simple['id'],
        "sourceFbid": MockUserData.user_with_friends['id']
    }

    quote_invalid_source = {
        "quote": "Here's to the crazy ones. The misfits. The rebels. The troublemakers. The round pegs in the square holes.",
        "reporterFbid": MockUserData.user_simple['id'],
        "sourceFbid": "invalid"
    }

    quote_invalid_reporter = {
        "quote": "Here's to the crazy ones. The misfits. The rebels. The troublemakers. The round pegs in the square holes.",
        "reporterFbid": "invalid",
        "sourceFbid": MockUserData.user_with_friends['id']
    }

    quote_same_source_reporter = {
        "quote": "The inability to quote yourself removes the narcissistic element from Echo, ensuring all of our content is original, spontaneous, honest, and funny",
        "reporterFbid": MockUserData.user_simple['id'],
        "sourceFbid": MockUserData.user_simple['id']
    }

    quote_normal_two = {
        "location": "Princeton, NJ",
        "location_lat": 23.342,
        "location_long": 364.41,
        "quote": "Echo is just another social mobile local iPhone app.",
        "reporterFbid": MockUserData.user_passive_spectator['id'],
        "sourceFbid": MockUserData.user_with_friends['id']
    }


class QuoteAPIHelpers(UserAPIHelpers):

    def add_quote(self, quote_dict, user_fbid = None):
        if user_fbid is None:
            user_fbid = quote_dict['reporterFbid']
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.post('/add_quote?token=%s' % token, data=dict(data=json.dumps(quote_dict)))

    def add_quote_to_db(self, quote_dict, deleted = False):
        source = User.query.filter_by(fbid=quote_dict['sourceFbid']).first()
        reporter = User.query.filter_by(fbid = quote_dict['reporterFbid']).first()
        if not source:
            return False
        if not reporter:
            return False
        quote = Quote(source.id, 
            reporter.id, 
            quote_dict['quote'], 
            quote_dict.get('location'), 
            quote_dict.get('location_lat'), 
            quote_dict.get('location_long'), 
            deleted)
        quote.echoers.append(reporter)
        db.session.add(quote)
        db.session.commit()
        return True

    def delete_quote(self, quote_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.delete('/delete_quote/%s?token=%s' % (quote_id, token))

    def get_quote(self, echo_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        rv = self.app.get('/get_quote?order_id=%s&token=%s' % (echo_id, token))
        rv = json.loads(rv.data)
        return rv

    def check_deleted_quotes(self, echo_ids, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        rv = self.app.post('/check_deleted_quotes?token=%s' % token, data=dict(data=json.dumps(echo_ids)))
        rv = json.loads(rv.data)
        return rv

    def get_quotes(self, user_fbid, limit, latest = None, oldest = None, profile_fbid = None):
        token = self.get_token_for_user_with_fbid(user_fbid)
        url = '/get_quotes?token=%s&limit=%s' % (token, limit)
        if latest is not None:
            url = (url + '&latest=%s') % latest
        if oldest is not None:
            url = (url + '&oldest=%s') % oldest
        if profile_fbid is not None:
            url = (url + '&profile_fbid=%s') % profile_fbid
        rv = self.app.get(url)
        rv = json.loads(rv.data)
        return rv


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
        self.add_quote(self.quote_minimal)
        self.assertEqual(Quote.query.count(), 1) # quote added

        quote = Quote.query.first()
        self.assert_is_same_quote_simple(quote, self.quote_minimal) # quote is fine

        self.add_quote(self.quote_normal)
        self.assertEqual(Quote.query.count(), 2) # quote added

        quote = Quote.query.all()[1]
        self.assert_is_same_quote_simple(quote, self.quote_normal) # quote is fine

    def BROKEN_test_add_quote_unicode(self):
        # TODO broken
        self.add_quote(self.quote_unicode)
        self.assertEqual(Quote.query.count(), 1) # quote added

        quote = Quote.query.first()
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


class MockCommentData():

    comment_for_quote_one = {
        "userFbid": MockUserData.user_simple['id'],
        "quoteId": "1",
        "comment": "Hahaha this is sooo true!! lol"
    }

    comment_for_quote_one_again = {
        "userFbid": MockUserData.user_with_friends['id'],
        "quoteId": "1",
        "comment": "Seconded!"
    }

    comment_for_quote_two = {
        "userFbid": MockUserData.user_simple['id'],
        "quoteId": "2",
        "comment": "This is for a different quote"
    }

    comment_for_one_by_passive = {
        "userFbid": MockUserData.user_passive_spectator['id'],
        "quoteId": "1",
        "comment": "This is from a user that's not the source nor the reporter"
    }

    comment_invalid_quote = {
        "userFbid": MockUserData.user_simple['id'],
        "quoteId": "invalid",
        "comment": "This is for an invalid quote id"
    }

    comment_unicode = {
        "userFbid": MockUserData.user_unicode_simple['id'],
        "quoteId": "1",
        "comment": "Айде един и на български"
    }


class CommentAPIHelpers(QuoteAPIHelpers):

    def add_comment(self, comment_dict, user_fbid = None):
        if user_fbid is None:
            user_fbid = comment_dict['userFbid']
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.post('/add_comment?token=%s' % token, data=dict(data=json.dumps(comment_dict)))

    def delete_comment(self, comment_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.delete('/delete_comment/%s?token=%s' % (comment_id, token))


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


# basically identical to the Echo stuff
class FavAPIHelpers(QuoteAPIHelpers):

    def add_fav(self, quote_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.post('/add_fav?token=%s' % token, data=dict(data=json.dumps({'quoteId': quote_id})))

    def delete_fav(self, quote_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.delete('/delete_fav/%s?token=%s' % (quote_id, token))

    def get_favs(self, quote_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        rv = self.app.get('/get_favs?quoteId=%s&token=%s' % (quote_id, token))
        rv = json.loads(rv.data)
        return rv


class TestFavAPI(TestBase, FavAPIHelpers, MockUserData, MockQuoteData):

    def setUp(self):
        TestBase.setUp(self)
        self.add_user(self.user_simple)
        self.add_user(self.user_with_friends)
        self.add_user(self.user_unicode_simple)
        self.add_quote(self.quote_minimal)
        self.add_quote(self.quote_normal)

    # ------------- helpers -------------

    # see if favs_res = get_favs(...) for a quote corresponds to the array user_ids_expected
    def assert_are_same_favs(self, favs_res, user_ids_expected):
        favs_dicts = []
        for user_id in user_ids_expected:
            user = User.query.filter_by(id=user_id).first()
            self.assertIsNotNone(user)
            fav_dict = {
                "fbid": user.fbid,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
            favs_dicts.append(fav_dict)
        self.assertItemsEqual(favs_res, favs_dicts)

    # ------------- tests -------------

    def test_add_fav(self):
        self.add_fav("1", self.user_simple['id'])
        self.assertEqual(Favorite.query.filter_by(quote_id=1, user_id=1).count(), 1) # added

        favorite = Favorite.query.first()
        user = User.query.first()
        quote = Quote.query.first()
        self.assertIn(favorite, user.favs) # added to user
        self.assertIn(favorite, quote.favs) # and to quote

    def test_add_fav_invalid(self):
        self.add_fav("1", "invalid")
        self.assertEqual(Favorite.query.count(), 0) # invalid user

        self.add_fav("invalid", self.user_simple['id'])
        self.assertEqual(Favorite.query.count(), 0) # invalid quote

        quote = Quote.query.first()
        quote.deleted = True
        db.session.commit()
        self.add_fav("1", self.user_simple['id'])
        self.assertEqual(Favorite.query.count(), 0) # quote deleted

        quote = Quote.query.first()
        quote.deleted = False
        db.session.commit()
        self.add_fav("1", self.user_simple['id'])
        self.assertEqual(Favorite.query.count(), 1) # added
        self.add_fav("1", self.user_simple['id'])
        self.assertEqual(Favorite.query.count(), 1) # duplicate ignored


    def test_delete_fav(self):
        self.add_fav("1", self.user_simple['id'])

        self.delete_fav("1", self.user_simple['id'])
        self.assertEqual(Favorite.query.count(), 0) # deleted

        self.add_fav("1", self.user_simple['id'])
        self.add_fav("1", self.user_with_friends['id'])
        self.assertEqual(Favorite.query.filter_by(quote_id=1).count(), 2) # re-add deleted fav

        self.delete_fav("1", self.user_simple['id'])
        self.assertEqual(Favorite.query.filter_by(quote_id=1).count(), 1) # selective delete
        quote = Quote.query.first()
        self.assertEqual(quote.favs[0].user_id, 2) # second fav remained

        self.delete_fav("1", self.user_simple['id'])
        self.assertEqual(Favorite.query.filter_by(quote_id=1).count(), 1) # repeat delete ignored

    def test_delete_fav_invalid(self):
        self.add_fav("1", self.user_simple['id'])

        self.delete_fav("1", "invalid")
        self.assertEqual(Favorite.query.count(), 1) # invalid user

        self.delete_fav("invalid", self.user_simple['id'])
        self.assertEqual(Favorite.query.count(), 1) # invalid quote

        quote = Quote.query.first()
        quote.deleted = True
        db.session.commit()
        self.delete_fav("1", self.user_simple['id'])
        self.assertEqual(Favorite.query.count(), 1) # quote deleted

        quote = Quote.query.first()
        quote.deleted = False
        db.session.commit()
        self.delete_fav("1", self.user_passive_spectator['id'])
        self.assertEqual(Favorite.query.count(), 1) # user hasn't favorited that quote

    def test_get_favs(self):
        self.add_fav("1", self.user_simple['id'])
        self.add_fav("1", self.user_with_friends['id'])
        self.add_fav("2", self.user_simple['id'])

        favs_res = self.get_favs("1", self.user_simple['id'])
        self.assert_are_same_favs(favs_res, [1, 2])
        favs_res = self.get_favs("2", self.user_simple['id'])
        self.assert_are_same_favs(favs_res, [1])


# basically identical to the Favs stuff
class EchoAPIHelpers(QuoteAPIHelpers):

    def add_echo(self, quote_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.post('/add_echo?token=%s' % token, data=dict(data=json.dumps({'quoteId': quote_id})))

    def delete_echo(self, quote_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.delete('/delete_echo/%s?token=%s' % (quote_id, token))

    def get_echoers(self, quote_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        rv = self.app.get('/get_echoers?quoteId=%s&token=%s' % (quote_id, token))
        rv = json.loads(rv.data)
        return rv


class TestEchoAPI(TestBase, EchoAPIHelpers, MockUserData, MockQuoteData):

    def setUp(self):
        TestBase.setUp(self)
        self.add_user(self.user_passive_spectator)
        self.add_user(self.user_unicode_simple)
        self.add_user(self.user_simple)
        self.add_user(self.user_with_friends)
        self.add_quote(self.quote_minimal)
        self.add_quote(self.quote_normal)

    # ------------- helpers -------------

    # see if favs_res = get_favs(...) for a quote corresponds to the array user_ids_expected
    def assert_are_same_echoers(self, echoers_res, user_ids_expected):
        echoers_dicts = []
        for user_id in user_ids_expected:
            user = User.query.filter_by(id=user_id).first()
            self.assertIsNotNone(user)
            echoer_dict = {
                "fbid": user.fbid,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
            echoers_dicts.append(echoer_dict)
        self.assertItemsEqual(echoers_res, echoers_dicts)

    # ------------- tests -------------

    def test_add_echo(self):
        self.add_echo("1", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.filter_by(quote_id=1, user_id=1).count(), 1) # added
        self.assertEqual(Echo.query.filter_by(quote_id=1).count(), 2) # in addition to default echo

        user = User.query.first()
        quote = Quote.query.first()
        self.assertIn(quote, user.echoes)
        self.assertIn(user, quote.echoers)

    def test_add_echo_invalid(self):
        self.add_echo("1", "invalid")
        self.assertEqual(Echo.query.count() - Quote.query.count(), 0) # invalid user

        self.add_echo("invalid", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 0) # invalid quote

        quote = Quote.query.first()
        quote.deleted = True
        db.session.commit()
        self.add_echo("1", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 0) # quote deleted

        quote = Quote.query.first()
        quote.deleted = False
        db.session.commit()
        self.add_echo("1", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # added
        self.add_echo("1", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # duplicate ignored

        self.add_echo("1", self.user_simple['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # source cannot echo
        self.add_echo("1", self.user_with_friends['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # reporter cannot echo either

    def test_delete_echo(self):
        self.add_echo("1", self.user_passive_spectator['id'])

        self.delete_echo("1", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 0) # deleted

        self.add_echo("1", self.user_passive_spectator['id'])
        self.add_echo("1", self.user_unicode_simple['id'])
        self.assertEqual(Echo.query.filter_by(quote_id=1).count() - 1, 2) # re-add deleted echo

        self.delete_echo("1", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.filter_by(quote_id=1).count() - 1, 1) # selective delete
        quote = Quote.query.first()
        self.assertEqual(quote.echoers[1].id, 2) # second echoer remained

        self.delete_echo("1", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.filter_by(quote_id=1).count() - 1, 1) # repeat delete ignored

    def test_delete_fav_invalid(self):
        self.add_echo("1", self.user_passive_spectator['id'])

        self.delete_echo("1", "invalid")
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # invalid user

        self.delete_echo("invalid", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # invalid quote

        quote = Quote.query.first()
        quote.deleted = True
        db.session.commit()
        self.delete_echo("1", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # quote deleted

        quote = Quote.query.first()
        quote.deleted = False
        db.session.commit()
        self.delete_echo("1", self.user_unicode_simple['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # you must have echoed to remove an echo
        self.delete_echo("1", self.user_simple['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # source cannot delete echo
        self.delete_echo("1", self.user_with_friends['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # reporter cannot delete echo either

    def test_get_echoers(self):
        self.add_echo("1", self.user_passive_spectator['id'])
        self.add_echo("1", self.user_unicode_simple['id'])
        self.add_echo("2", self.user_passive_spectator['id'])

        echoers_res = self.get_echoers("1", self.user_simple['id'])
        self.assert_are_same_echoers(echoers_res, [1, 2])
        echoers_res = self.get_echoers("2", self.user_simple['id'])
        self.assert_are_same_echoers(echoers_res, [1])


class NotifAPIHelpers(QuoteAPIHelpers, CommentAPIHelpers, FavAPIHelpers, EchoAPIHelpers):

    def get_notifications(self, unread_only, limit, clear, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        if limit is None:
            rv = self.app.get('/get_notifications?unread_only=%s&clear=%s&token=%s' % (unread_only, clear, token))
        else:
            rv = self.app.get('/get_notifications?unread_only=%s&limit=%s&clear=%s&token=%s' % (unread_only, limit, clear, token))
        rv = json.loads(rv.data)
        return rv

    def get_notifprefs(self, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        rv = self.app.get('/get_notifprefs?token=%s' % token)
        rv = json.loads(rv.data)
        return rv

    def set_notifprefs(self, prefs_dict, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.post('/set_notifprefs?token=%s' % token, data=dict(data=json.dumps(prefs_dict)))


class TestNotifAPI(TestBase, NotifAPIHelpers, MockUserData, MockQuoteData, MockCommentData):

    def setUp(self):
        TestBase.setUp(self)
        self.add_user(self.user_simple) # reporter
        self.add_user(self.user_with_friends) # source

    # ------------- helpers -------------

    # check if db entry notif after add_notification is the same as notif_dict
    def assert_is_same_notif(self, notif, notif_dict):
        self.assertEqual(notif.user_id, notif_dict['user_id'])
        self.assertEqual(notif.type, notif_dict['type'])
        self.assertEqual(notif.quote_id, notif_dict['quote_id'])
        self.assertEqual(notif.echo_id, notif_dict['echo_id'])

    # ------------- tests -------------

    def test_add_quote_notification(self):
        self.add_quote(self.quote_minimal)
        reporter = User.query.all()[0]
        source = User.query.all()[1]
        self.assertEqual(Notification.query.filter_by(user_id=reporter.id).count(), 1) # reporter sent the notification
        self.assertEqual(Notification.query.filter_by(user_id=source.id).count(), 0) # and not the source

        notif = Notification.query.filter(Notification.recipients.any(User.id==source.id)).order_by(desc(Notification.id)).first()
        self.assertIsNotNone(notif) # source got the notif
        self.assert_is_same_notif(notif, {'user_id': reporter.id, 'type': 'quote', 'quote_id': 1, 'echo_id': 1}) # and it's correct

    def test_add_comment_notification(self):
        self.add_quote(self.quote_minimal)

        # source comment
        self.add_comment(self.comment_for_quote_one_again)
        reporter = User.query.all()[0]
        source = User.query.all()[1]
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==source.id), Notification.type=='comment').count(), 0) # source didn't get it b/c it's his comment
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==reporter.id), Notification.type=='comment').count(), 1) # reporter, however, got it

        notif = Notification.query.filter(Notification.recipients.any(User.id==reporter.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': source.id, 'type': 'comment', 'quote_id': 1, 'echo_id': 1}) # and it's correct
        
        # reporter comment
        self.add_comment(self.comment_for_quote_one)
        reporter = User.query.all()[0]
        source = User.query.all()[1]
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==source.id), Notification.type=='comment').count(), 1) # source got it
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==reporter.id), Notification.type=='comment').count(), 1) # reporter didn't get it b/c it's his comment

        notif = Notification.query.filter(Notification.recipients.any(User.id==source.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': reporter.id, 'type': 'comment', 'quote_id': 1, 'echo_id': 1}) # and it's correct

        # rando comment with no friends
        self.add_user(self.user_passive_spectator)
        self.add_comment(self.comment_for_one_by_passive)
        self.assertEqual(Notification.query.count(), 3) # nobody got a notification b/c rando is not friends w/ anyone

        # rando befriends reporter and source and comments again
        self.add_user(self.user_passive_spectator_with_friends)
        self.add_comment(self.comment_for_one_by_passive)
        reporter = User.query.all()[0]
        source = User.query.all()[1]
        rando = User.query.filter_by(fbid=self.user_passive_spectator_with_friends['id']).first()
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==source.id), Notification.type=='comment').count(), 2) # source got it this time
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==reporter.id), Notification.type=='comment').count(), 2) # so did reporter
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==rando.id)).count(), 0) # still nothing for poor rando

        notif = Notification.query.filter(Notification.recipients.any(User.id==source.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': rando.id, 'type': 'comment', 'quote_id': 1, 'echo_id': 1}) # and it's correct for source

        notif = Notification.query.filter(Notification.recipients.any(User.id==reporter.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': rando.id, 'type': 'comment', 'quote_id': 1, 'echo_id': 1}) # and for reporter

    def test_add_echo_notification(self):
        self.add_quote(self.quote_minimal)
        self.add_user(self.user_passive_spectator_with_friends)

        # echo
        self.add_echo("1", self.user_passive_spectator_with_friends['id'])
        reporter = User.query.all()[0]
        source = User.query.all()[1]
        rando = User.query.filter_by(fbid=self.user_passive_spectator_with_friends['id']).first()
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==source.id), Notification.type=='echo').count(), 1) # source got notified
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==reporter.id), Notification.type=='echo').count(), 1) # so did reporter
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==rando.id)).count(), 0) # still nothing for poor rando

        notif = Notification.query.filter(Notification.recipients.any(User.id==source.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': rando.id, 'type': 'echo', 'quote_id': 1, 'echo_id': 1}) # and it's correct for source

        notif = Notification.query.filter(Notification.recipients.any(User.id==reporter.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': rando.id, 'type': 'echo', 'quote_id': 1, 'echo_id': 1}) # and for reporter

    def test_add_fav_notification(self):
        self.add_quote(self.quote_minimal)
        self.add_user(self.user_passive_spectator_with_friends)

        # source favs
        self.add_fav("1", self.user_with_friends['id'])
        reporter = User.query.all()[0]
        source = User.query.all()[1]
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==source.id), Notification.type=='fav').count(), 0) # source didn't get it b/c it's his fav
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==reporter.id), Notification.type=='fav').count(), 1) # reporter, however, got it

        notif = Notification.query.filter(Notification.recipients.any(User.id==reporter.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': source.id, 'type': 'fav', 'quote_id': 1, 'echo_id': 1}) # and it's correct
        
        # reporter favs
        self.add_fav("1", self.user_simple['id'])
        reporter = User.query.all()[0]
        source = User.query.all()[1]
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==source.id), Notification.type=='fav').count(), 1) # source got it
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==reporter.id), Notification.type=='fav').count(), 1) # reporter didn't get it b/c it's his comment

        notif = Notification.query.filter(Notification.recipients.any(User.id==source.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': reporter.id, 'type': 'fav', 'quote_id': 1, 'echo_id': 1}) # and it's correct

        # rando favs
        self.add_fav("1", self.user_passive_spectator_with_friends['id'])
        reporter = User.query.all()[0]
        source = User.query.all()[1]
        rando = User.query.filter_by(fbid=self.user_passive_spectator_with_friends['id']).first()
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==source.id), Notification.type=='fav').count(), 2) # source got notified
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==reporter.id), Notification.type=='fav').count(), 2) # so did reporter
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==rando.id)).count(), 0) # still nothing for poor rando

        notif = Notification.query.filter(Notification.recipients.any(User.id==source.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': rando.id, 'type': 'fav', 'quote_id': 1, 'echo_id': 1}) # and it's correct for source

        notif = Notification.query.filter(Notification.recipients.any(User.id==reporter.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': rando.id, 'type': 'fav', 'quote_id': 1, 'echo_id': 1}) # and for reporter

    def BROKEN_test_add_notification_unicode(self):
        #self.add_user(self.user_unicode_simple)
        #self.add_quote(self.quote_unicode) # unicode user is source

        #self.add_quote(self.quote_unicode_flipped) # unicode user is reporter
        # TODO broken
        pass

    def test_get_notifications(self):
        self.add_user(self.user_passive_spectator_with_friends)
        self.add_quote(self.quote_minimal)
        self.add_comment(self.comment_for_quote_one)
        self.add_echo("1", self.user_passive_spectator_with_friends['id'])
        self.add_fav("1", self.user_simple['id'])
        notifs_res = self.get_notifications(0, None, 0, self.user_with_friends['id'])
        self.assertEqual(len(notifs_res), 4) # we got all four

        notifs_res_expected = [
            {
                '_id': '1',
                'order_id': '1',
                'formatted-text': {
                    'text': 
                    '%s favorited your quote: "%s"' % (self.user_simple['name'], self.quote_minimal['quote']), 
                    'bold': [
                        {
                            'length': len(self.user_simple['name']),
                            'location': 0
                        }
                    ]
                },
                'unread': True,
                'type': 'fav'                
            },
            {
                '_id': '1',
                'order_id': '1',
                'formatted-text': {
                    'text': 
                    '%s echoed your quote: "%s"' % (self.user_passive_spectator['name'], self.quote_minimal['quote']), 
                    'bold': [
                        {
                            'length': len(self.user_passive_spectator['name']),
                            'location': 0
                        }
                    ]
                },
                'unread': True,
                'type': 'echo'
            },
            {
                '_id': '1',
                'order_id': '1',
                'formatted-text': {
                    'text': 
                    '%s commented on your quote.' % (self.user_simple['name']), 
                    'bold': [
                        {
                            'length': len(self.user_simple['name']),
                            'location': 0
                        }
                    ]
                },
                'unread': True,
                'type': 'comment'
            },
            {
                '_id': '1',
                'order_id': '1',
                'formatted-text': {
                    'text': 
                    '%s posted a quote by you!' % (self.user_simple['name']), 
                    'bold': [
                        {
                            'length': len(self.user_simple['name']),
                            'location': 0
                        }
                    ]
                },
                'unread': True,
                'type': 'quote'
            },
        ]

        for i in range(4):
            notif_res = self.get_notifications(1, 1, 1, self.user_with_friends['id'])[0]
            self.assertIn('timestamp', notif_res)
            del notif_res['timestamp'] # changes sometimes +- 1 sec
            self.assertEqual(notif_res, notifs_res_expected[i]) # extract them one by one and compare

    def test_set_notifprefs(self):
        # defaults
        self.set_notifprefs({}, self.user_simple['id'])
        user = User.query.first()
        self.assertEqual(user.notifprefs.quotes, 1)
        self.assertEqual(user.notifprefs.echoes, 1)
        self.assertEqual(user.notifprefs.comments, 1)
        self.assertEqual(user.notifprefs.favs, 1)

        # change some
        self.set_notifprefs({'quotes': 0, 'favs': 0}, self.user_simple['id'])
        user = User.query.first()
        self.assertEqual(user.notifprefs.quotes, 0)
        self.assertEqual(user.notifprefs.echoes, 1)
        self.assertEqual(user.notifprefs.comments, 1)
        self.assertEqual(user.notifprefs.favs, 0)

        # change others
        self.set_notifprefs({'echoes': 0, 'comments': 0}, self.user_simple['id'])
        user = User.query.first()
        self.assertEqual(user.notifprefs.quotes, 0)
        self.assertEqual(user.notifprefs.echoes, 0)
        self.assertEqual(user.notifprefs.comments, 0)
        self.assertEqual(user.notifprefs.favs, 0)

        # change all back
        self.set_notifprefs({'echoes': 1, 'comments': 1, 'quotes': 1, 'favs': 1}, self.user_simple['id'])
        user = User.query.first()
        self.assertEqual(user.notifprefs.quotes, 1)
        self.assertEqual(user.notifprefs.echoes, 1)
        self.assertEqual(user.notifprefs.comments, 1)
        self.assertEqual(user.notifprefs.favs, 1)

    def test_get_notifprefs(self):
        notifprefs = self.get_notifprefs(self.user_simple['id'])
        self.assertEqual(notifprefs, {'quotes': 1, 'favs': 1, 'comments': 1, 'echoes': 1}) # defaults

        user = User.query.first()
        user.notifprefs.quotes = 0
        user.notifprefs.comments = 0
        db.session.commit()
        notifprefs = self.get_notifprefs(self.user_simple['id'])
        self.assertEqual(notifprefs, {'quotes': 0, 'favs': 1, 'comments': 0, 'echoes': 1})

        user = User.query.first()
        user.notifprefs.echoes = 0
        user.notifprefs.favs = 0
        db.session.commit()
        notifprefs = self.get_notifprefs(self.user_simple['id'])
        self.assertEqual(notifprefs, {'quotes': 0, 'favs': 0, 'comments': 0, 'echoes': 0})


class MiscAPIHelpers(UserAPIHelpers):

    def add_feedback(self, feedback_dict, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.post('/add_feedback?token=%s' % token, data=dict(data=json.dumps(feedback_dict)))


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
