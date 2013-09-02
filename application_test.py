# -*- coding: utf-8 -*-

import os
import unittest
import tempfile
import json
from flask.ext.sqlalchemy import SQLAlchemy
from pprint import pprint
import time
from copy import copy

import application
import model
from model import db
from model import User, Quote, Comment, Favorite, Echo
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


class MockUserData():

    user_simple = {
        "id": "12345",
        "email": "example@gmail.com",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc7/370214_100000486204833_1328204472_q.jpg",
        "name": "Lonely Loner", 
        "friends": [],
        "unfriends": []
    }

    user_with_friends = {
        "id": "67890",
        "email": "yolobro@gmail.com",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc6/274340_1778127543_1201810974_q.jpg",
        "name": "John Smith", 
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
        "name": "John Smith", 
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
        "unfriends": [user_with_friends['friends'][1]['id'], user_with_friends['friends'][2]['id'], "1000000000000000000"]
    }

    user_unicode_simple = {
        "id": "54321",
        "email": "baihui@abv.bg",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc7/370214_100000486204833_1328204472_qq123.jpg",
        "name": "Бай Хуй",
        "friends": [],
        "unfriends": []
    }

class UserAPIHelpers():

    def get_token_for_user_with_fbid(self, user_fbid):
        rv = self.app.get('/get_token?fbid=%s&token=universal_access_token_TODO_this_must_be_gone_ASAP--see_facebook_test_users' % user_fbid)
        rv = json.loads(rv.data)
        return rv['access_token'];

    def add_user(self, user_dict):
        token = self.get_token_for_user_with_fbid(user_dict['id'])
        self.app.post('/add_user?token=%s' % token, data=dict(data=json.dumps(user_dict)))


class TestUserAPI(TestBase, UserAPIHelpers, MockUserData):

    # ------------- helpers -------------

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

    def assert_friends_reciprocity(self, user):
        self.assertIsNotNone(user)
        for friend in user.all_friends:
            self.assertTrue(user in friend.all_friends)

    # ------------- tests -------------

    def _test_get_token(self):
        token = self.get_token_for_user_with_fbid(self.user_simple['id'])
        self.assertEqual(User.query.count(), 1) # hollow profile is created

    def _test_add_user_simple(self):
        self.add_user(self.user_simple)
        self.assertEqual(User.query.count(), 1) # user info is updated (no new user is created)

        user = User.query.first()
        self.assert_is_same_user_simple(user, self.user_simple)

    def _test_add_user_with_friends(self):
        self.add_user(self.user_with_friends)
        self.assertEqual(User.query.count(), 1 + len(self.user_with_friends['friends'])) # friends are added as users

        user = User.query.first()
        self.assert_is_same_user_with_friends(user, self.user_with_friends) # user and friend data is ok
        self.assert_friends_reciprocity(user) # friend relationships are symmetrical

    def _test_add_user_with_friends_extended(self):
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

    def _test_user_unicode(self):
        self.add_user(self.user_unicode_simple)
        self.assertEqual(User.query.count(), 1) # user added

        user = User.query.first()
        self.assert_is_same_user_simple(user, self.user_unicode_simple)

    def _test_user_invalid(self):
        # TODO implement once we have test users
        pass


class MockQuoteData():

    quote_minimal = {
        "quote": "Here’s to the crazy ones. The misfits. The rebels. The troublemakers. The round pegs in the square holes.",
        "reporterFbid": MockUserData.user_simple['id'],
        "sourceFbid": MockUserData.user_with_friends['id']
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

    quote_invalid_source = {
        "quote": "Here's to the crazy ones. The misfits. The rebels. The troublemakers. The round pegs in the square holes.",
        "reporterFbid": MockUserData.user_simple['id'],
        "sourceFbid": "100000000000000001"
    }

    quote_invalid_reporter = {
        "quote": "Here's to the crazy ones. The misfits. The rebels. The troublemakers. The round pegs in the square holes.",
        "reporterFbid": "100000000000000001",
        "sourceFbid": MockUserData.user_with_friends['id']
    }

    quote_same_source_reporter = {
        "quote": "The inability to quote yourself removes the narcissistic element from Echo, ensuring all of our content is original, spontaneous, honest, and funny",
        "reporterFbid": MockUserData.user_simple['id'],
        "sourceFbid": MockUserData.user_simple['id']
    }

class QuoteAPIHelpers(UserAPIHelpers):

    def add_quote(self, quote_dict, user_fbid = None):
        if user_fbid is None:
            user_fbid = quote_dict['reporterFbid']
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.post('/add_quote?token=%s' % token, data=dict(data=json.dumps(quote_dict)))

    def add_quote_to_db(self, quote_dict):
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
            False)
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


class TestQuoteAPI(TestBase, QuoteAPIHelpers, MockUserData, MockQuoteData):

    def setUp(self):
        TestBase.setUp(self)
        self.add_user(self.user_simple)
        self.add_user(self.user_with_friends)
        self.add_user(self.user_unicode_simple)

    # ------------- helpers -------------

    # check if the db entry quote = add_quote(quote_dict) is consistent with quote_dict
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
    def assert_is_consistent_quote_res(self, quote_res, user_fbid):
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


    # ------------- tests -------------

    def _test_add_quote(self):
        self.add_quote(self.quote_minimal)
        self.assertEqual(Quote.query.count(), 1) # quote added

        quote = Quote.query.first()
        self.assert_is_same_quote_simple(quote, self.quote_minimal) # quote is fine

        self.add_quote(self.quote_normal)
        self.assertEqual(Quote.query.count(), 2) # quote added

        quote = Quote.query.all()[1]
        self.assert_is_same_quote_simple(quote, self.quote_normal) # quote is fine

    def test_add_quote_unicode(self):
        self.add_quote(self.quote_unicode)
        self.assertEqual(Quote.query.count(), 1) # quote added

        quote = Quote.query.first()
        self.assert_is_same_quote_simple(quote, self.quote_unicode) # quote is fine

    def _test_add_quote_invalid(self):
        self.add_quote(self.quote_invalid_source)
        self.assertEqual(Quote.query.count(), 0) # invalid source

        self.add_quote(self.quote_invalid_reporter, self.user_simple['id'])
        self.assertEqual(Quote.query.count(), 0) # invalid reporter

        self.add_quote(self.quote_same_source_reporter)
        self.assertEqual(Quote.query.count(), 0) # source = reporter        

    def _test_delete_quote(self):
        self.add_quote(self.quote_minimal)
        self.delete_quote("1", self.quote_minimal['reporterFbid'])
        self.assertEqual(Quote.query.count(), 1) # do not remove from db
        quote = Quote.query.first()
        self.assert_is_same_quote_simple(quote, self.quote_minimal, True) # deleted by reporter

        self.add_quote(self.quote_minimal)
        self.delete_quote("2", self.quote_minimal['sourceFbid'])
        quote = Quote.query.all()[1]
        self.assert_is_same_quote_simple(quote, self.quote_minimal, True) # deleted by source

    def _test_delete_quote_invalid(self):
        self.add_quote(self.quote_minimal)

        self.delete_quote("1", "100000000000000001")
        quote = Quote.query.first()
        self.assert_is_same_quote_simple(quote, self.quote_minimal) # not deleted -- invalid user

        self.delete_quote("1", self.user_unicode_simple['id'])
        quote = Quote.query.first()
        self.assert_is_same_quote_simple(quote, self.quote_minimal) # not deleted -- user is not reporter nor source

        self.delete_quote("2", self.quote_minimal['reporterFbid'])
        quote = Quote.query.first()
        self.assert_is_same_quote_simple(quote, self.quote_minimal) # not deleted -- wrong quote id

    def _test_get_quote_simple(self):
        self.assertTrue(self.add_quote_to_db(self.quote_minimal))
        quote_res = self.get_quote("1", self.user_simple['id'])
        self.assert_is_consistent_quote_res(quote_res, self.user_simple['id'])

if __name__ == '__main__':
    unittest.main()
