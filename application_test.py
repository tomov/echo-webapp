# -*- coding: utf-8 -*-

import os
import unittest
import tempfile
import json
from flask.ext.sqlalchemy import SQLAlchemy
from pprint import pprint
import time

import application
import model
from model import db
from model import User, Quote, Echo, Comment
from constants import *
from test_data import *
from util import *

TEST_DATABASE_NAME = 'echo_webapp_test'
TEST_DATABASE_URI = DatabaseConstants.DATABASE_URI_TEMPLATE % TEST_DATABASE_NAME # DO NOT FUCK THIS UP! or you'll erase the real db....

#: these lines will be used throughout for debugging purposes
print '===> _before: using db -- ' + application.app.config['SQLALCHEMY_DATABASE_URI']

class ApplicationTestCase(unittest.TestCase):


    def setUp(self): #: called before each individual test function is run
        ''' Uncomment this to use a tempfile for db
        self.db_fd, application.app.config['DATABASE'] = tempfile.mkstemp()
        application.app.config['TESTING'] = True

        application.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + application.app.config['DATABASE']
        '''

        application.app.config['SQLALCHEMY_DATABASE_URI'] = TEST_DATABASE_URI

        print '===> setup: using db -- ' + application.app.config['SQLALCHEMY_DATABASE_URI']

        db.app = application.app
        self.app = application.app.test_client()

        db.create_all() #: initialize all tables

    def tearDown(self): #: called after the test is run (close shit)
        # os.close(self.db_fd)
        # os.unlink(application.app.config['DATABASE'])
        
        db.session.remove() # REALLY IMPORTANT to do this before the one below, otherwise can't run more than one test
        db.drop_all() #: get rid of tables

        print '===> teardown: end'

    ## TODO this is legacy from Chris, see how can possibly make useful 
    def add_sample_data(self):
        #: sample users
        user1 = User(1, 'user1@somesite.com', 'User', 'One', None, None, True)
        user2 = User(2, 'user2@somesite.com', 'User', 'Two', None, None, True)
        user3 = User(3, 'user3@somesite.com', 'User', 'Three', None, None, True)

        user1.friends.append(user2)
        user1.friends.append(user3)
        user2.friends.append(user1)
        user3.friends.append(user1)

        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)

        db.session.commit()

        #: sample quotes
        entry_user1 = User.query.filter_by(fbid=1).first()
        entry_user2 = User.query.filter_by(fbid=2).first()
        entry_user3 = User.query.filter_by(fbid=3).first()
        
        quote1 = Quote(entry_user1.id, entry_user2.id, 'Test Q1 -- Source: 1, Reporter: 2', 'Princeton, NJ', False)
        quote2 = Quote(entry_user1.id, entry_user3.id, 'Test Q2 -- Source: 1, Reporter: 3', 'Princeton, NJ', False)
        quote3 = Quote(entry_user2.id, entry_user1.id, 'Test Q3 -- Source: 2, Reporter: 1', 'Princeton, NJ', False)

        db.session.add(quote1)
        db.session.add(quote2)
        db.session.add(quote3)

        db.session.commit() #: commit changes to db, otherwise it will rollback

    def assert_is_same_user(self, user, json):
        assert user is not None
        assert user.fbid == json['id']
        assert user.email == json['email']
        assert user.picture_url == json['picture_url']
        first, last = split_name(json['name'])
        assert user.first_name == first
        assert user.last_name == last
        assert len(user.friends) == len(json['friends'])

        for friend in json['friends']:
            user = User.query.filter_by(fbid = friend["id"]).first()
            assert user is not None
            first, last = split_name(friend['name'])
            assert user.first_name == first
            assert user.last_name == last
            assert user.picture_url == friend['picture']['data']['url']


    def assert_is_same_quote(self, quote, json):
        source = User.query.filter_by(fbid = json['sourceFbid']).first()
        assert source
        assert quote.source_id == source.id
        reporter = User.query.filter_by(fbid = json['reporterFbid']).first()
        assert reporter
        assert quote.reporter_id == reporter.id 
        assert quote.location == json['location']
        assert quote.location_lat == json['location_lat']
        assert quote.location_long == json['location_long']
        assert quote.content == json['quote']

    def assert_is_same_comment(self, comment, json):
        user = User.query.filter_by(fbid = json['userFbid']).first()
        assert user 
        assert comment.user_id == user.id
        quote = Quote.query.filter_by(id = json['quoteId']).first()
        assert quote
        assert comment.quote_id == quote.id
        assert comment.content == json['comment']

    ## note the first json version is the one returned by the api call, the second one is the one stored in the test_data file (so it has less fields e.g. no timestamp and no id)
    def assert_is_same_quote_jsononly(self, quote, json):
        assert quote['location'] == json['location']
        assert quote['location_lat'] == json['location_lat']
        assert quote['location_long'] == json['location_long']
        assert quote['quote'] == json['quote']
        assert str(quote['sourceFbid']) == str(json['sourceFbid'])
        assert str(quote['reporterFbid']) == str(json['reporterFbid'])
        assert int(quote['timestamp']) > 1000000
        assert int(quote['_id']) > 0

    def assert_is_same_list_of_quotes(self, quotes, json_list):
        assert len(quotes) == len(json_list)
        quotes = sorted(quotes, key = lambda k: k['_id']) # in increasing order... for convenience
        for quote, json in zip(quotes, json_list):
            self.assert_is_same_quote_jsononly(quote, json)

     ## note the first json version is the one returned by the api call, the second one is the one stored in the test_data file (so it has less fields e.g. no timestamp and no id)
    def assert_is_same_comment_jsononly(self, comment, json, is_friend):
        assert str(comment['fbid']) == str(json['userFbid'])
        assert str(comment['comment']) == str(json['comment'])
        if not is_friend:
            user = User.query.filter_by(fbid = json['userFbid']).first()
            assert user
            assert comment['name'] == user.first_name + ' ' + user.last_name
            assert comment['picture_url'] == user.picture_url
        else:
            assert 'name' not in comment
            assert 'picture_url' not in comment 
        quote_id = Comment.query.filter_by(id = comment['id']).first().quote_id
        assert quote_id == json['quoteId']
        assert int(comment['timestamp']) > 1000000
        assert int(comment['id']) > 0

 
# ----------------------------------------------------------------------
# Tests. Note: test functions must begin with "test" i.e. test_something
# ----------------------------------------------------------------------
   
    def test_util(self):
        print "\n ------- begin test util ------\n"

        first, last = split_name('')
        assert first == last
        assert last == ''

        first, last = split_name('hello')
        assert first == 'hello'
        assert last == ''

        first, last = split_name('Jacob Simon')
        assert first == 'Jacob'
        assert last == 'Simon'

        first, last = split_name('Momchil Slavchev Tomov')
        assert first == 'Momchil'
        assert last == 'Tomov'

        first, last = split_name(u'Момчил Славчев Томов') # test unicode
        assert first == 'Момчил'
        assert last == 'Томов'

        print "\n ------- end test util ------- \n"


    def test_single_register(self):
        # insert a single user and make sure everything's correct
        print "\n------- begin single test -------\n"

        assert len(User.query.all()) == 0
        george_dump = json.dumps(RandomUsers.george)
        rv = self.app.post('/add_user', data = dict(data=george_dump))
        assert len(User.query.all()) == 5   # hardcoded for clarity

        user = User.query.filter_by(fbid = RandomUsers.george['id']).first()
        self.assert_is_same_user(user, RandomUsers.george)
        assert user.registered

        print "\n-------- end single test --------\n"

    #def test_register_errors(self):
        # hit all the corner cases of adding a user TODO


    def test_single_quote(self):
        # insert a single quote and make sure everything's fine
        print "\n ------ begin test few quotes ------\n"

        george_dump = json.dumps(RandomUsers.george)
        self.app.post('/add_user', data = dict(data=george_dump))

        assert len(Quote.query.all()) == 0
        quote_dump = json.dumps(RandomQuotes.contemporary_art)
        rv = self.app.post('/add_quote', data = dict(data=quote_dump))
        assert len(Quote.query.all()) == 1

        quote = Quote.query.all()[0]
        self.assert_is_same_quote(quote, RandomQuotes.contemporary_art)

        print "\n ------ end test few quotes ------\n"

    #def test_single_quote_errors(self): TODO

    def test_single_comment(self):
        print "\n ---- begin test single comment ----- \n"

        ## add user and quote
        george_dump = json.dumps(RandomUsers.george)
        self.app.post('/add_user', data = dict(data=george_dump))
        quote_dump = json.dumps(RandomQuotes.contemporary_art)
        rv = self.app.post('/add_quote', data = dict(data=quote_dump))

        ## add comment and make sure it's correct in the database
        assert len(Comment.query.all()) == 0
        comment_dump = json.dumps(RandomComments.thissucks)
        rv = self.app.post('/add_comment', data = dict(data=comment_dump))
        assert len(Comment.query.all()) == 1

        comment = Comment.query.all()[0]
        self.assert_is_same_comment(comment, RandomComments.thissucks)

        print "\n ----- end test single comment ---- \n"

    def test_get_quote(self):
        print "\n-------- begin test get quote ---\n"

        ## add users, quote, a bunch of comments, favorites, and echoes
        george_dump = json.dumps(RandomUsers.george)
        self.app.post('/add_user', data = dict(data=george_dump))
        zdravko_dump = json.dumps(RandomUsers.zdravko) # b/c he's not a friend of george's so he's not added but he comments
        self.app.post('/add_user', data = dict(data=zdravko_dump))
        quote_dump = json.dumps(RandomQuotes.contemporary_art)
        rv = self.app.post('/add_quote', data = dict(data=quote_dump))

        ## make sure the correct quote is returned before adding comments
        rv = self.app.get('/get_quote?id=1&userFbid=' + RandomUsers.george['id'])
        rv = json.loads(rv.data)
        self.assert_is_same_quote_jsononly(rv, RandomQuotes.contemporary_art)
        assert len(rv['comments']) == 0

        ## now add some comments
        comment_dump = json.dumps(RandomComments.thissucks)
        rv = self.app.post('/add_comment', data = dict(data=comment_dump))
        comment_dump = json.dumps(RandomComments.funnyquote)
        time.sleep(1) # b/c we order by created, we need to have different create times
        rv = self.app.post('/add_comment', data = dict(data=comment_dump))
        comment_dump = json.dumps(RandomComments.angelayousuck) # this comment is not by a friend of george, so additional info must be returned for him by get_quote
        time.sleep(1) # b/c we order by created, we need to have different create times
        rv = self.app.post('/add_comment', data = dict(data=comment_dump))

        ## make sure the correct quote is returned again
        rv = self.app.get('/get_quote?id=1&userFbid=' + RandomUsers.george['id'])
        rv = json.loads(rv.data)
        self.assert_is_same_quote_jsononly(rv, RandomQuotes.contemporary_art)

        ## also make sure it has the correct comments in the correct order
        assert rv['comments']
        assert len(rv['comments']) == 3
        self.assert_is_same_comment_jsononly(rv['comments'][0], RandomComments.thissucks, True)
        self.assert_is_same_comment_jsononly(rv['comments'][1], RandomComments.funnyquote, True)
        self.assert_is_same_comment_jsononly(rv['comments'][2], RandomComments.angelayousuck, False)

        print "\n------- end test get quote ---- \n"

    def test_get_quotes(self):
        print "\n------- begin get quotes ------\n"

        ## insert users
        assert len(User.query.all()) == 0
        george_dump = json.dumps(RandomUsers.george)
        deepika_dump = json.dumps(RandomUsers.deepika)
        angela_dump = json.dumps(RandomUsers.angela)
        zdravko_dump = json.dumps(RandomUsers.zdravko)
        rv = self.app.post('/add_user', data = dict(data=george_dump))
        rv = self.app.post('/add_user', data = dict(data=deepika_dump))
        rv = self.app.post('/add_user', data = dict(data=angela_dump))
        rv = self.app.post('/add_user', data = dict(data=zdravko_dump))
        assert len(User.query.all()) == 7 # hardcoded for clarity and extra security
        assert len(User.query.filter(User.registered == True).all()) == 4

        ## make sure users are ok
        angela = User.query.filter_by(fbid = RandomUsers.angela['id']).first()
        self.assert_is_same_user(angela, RandomUsers.angela)
        assert angela.registered
        deepika = User.query.filter_by(fbid = RandomUsers.deepika['id']).first()
        self.assert_is_same_user(deepika, RandomUsers.deepika)
        assert deepika.registered
        george = User.query.filter_by(fbid = RandomUsers.george['id']).first()
        self.assert_is_same_user(george, RandomUsers.george)
        assert george.registered
        zdravko = User.query.filter_by(fbid = RandomUsers.zdravko['id']).first()
        self.assert_is_same_user(zdravko, RandomUsers.zdravko)
        assert zdravko.registered

        ## insert quote by george (reporter) and angela (source)
        assert len(Quote.query.all()) == 0
        contemporary_art = json.dumps(RandomQuotes.contemporary_art)
        rv = self.app.post('/add_quote', data = dict(data=contemporary_art))

        ## make sure zdravko <---> angela <----> george <---> deepika can see it 
        ## here the <--->'s mark friendships
        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.zdravko['id'])
        rv_list = json.loads(rv.data)
        assert len(rv_list) == 1
        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.angela['id'])
        rv_list = json.loads(rv.data)
        assert len(rv_list) == 1
        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.george['id'])
        rv_list = json.loads(rv.data)
        assert len(rv_list) == 1
        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.deepika['id'])
        rv_list = json.loads(rv.data)
        assert len(rv_list) == 1

        ## insert quote by angela (reporter) and george (source)
        girlfriend = json.dumps(RandomQuotes.girlfriend)
        time.sleep(1) # so the created field is different
        rv = self.app.post('/add_quote', data = dict(data=girlfriend))
        ## insert quote by angela (reporter) and cameron (source)
        anotherquote = json.dumps(RandomQuotes.anotherquote)
        time.sleep(1)
        rv = self.app.post('/add_quote', data = dict(data=anotherquote))
        ## insert quote by deepika (reporter) and george (source)
        andanotherone = json.dumps(RandomQuotes.andanotherone)
        time.sleep(1)
        rv = self.app.post('/add_quote', data = dict(data=andanotherone))

        ## make sure everyone sees what they must
        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.zdravko['id'])
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.contemporary_art, RandomQuotes.girlfriend, RandomQuotes.anotherquote])

        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.angela['id'])
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.contemporary_art, RandomQuotes.girlfriend, RandomQuotes.anotherquote, RandomQuotes.andanotherone])

        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.george['id'])
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.contemporary_art, RandomQuotes.girlfriend, RandomQuotes.anotherquote, RandomQuotes.andanotherone])

        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.deepika['id'])
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.contemporary_art, RandomQuotes.girlfriend, RandomQuotes.andanotherone])


        ## make sure the me page is working
        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.zdravko['id'] + '&type=me')
        rv_list = json.loads(rv.data)
        assert len(rv_list) == 0

        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.angela['id'] + '&type=me')
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.contemporary_art, RandomQuotes.girlfriend, RandomQuotes.anotherquote])

        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.george['id'] + '&type=me')
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.contemporary_art, RandomQuotes.girlfriend, RandomQuotes.andanotherone])

        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.deepika['id'] + '&type=me')
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.andanotherone])

        ## test oldest and latest
        quote = Quote.query.filter_by(content=RandomQuotes.girlfriend['quote']).first()
        timestamp = time.mktime(quote.created.timetuple()) 

        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.george['id'] + '&latest=' + str(int(timestamp)))
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.anotherquote, RandomQuotes.andanotherone])

        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.george['id'] + '&oldest=' + str(int(timestamp)))
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.contemporary_art])

        ## test lastest/oldest with me page 
        quote = Quote.query.filter_by(content=RandomQuotes.girlfriend['quote']).first()
        timestamp = time.mktime(quote.created.timetuple())

        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.george['id'] + '&type=me&latest=' + str(int(timestamp)))
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.andanotherone])

        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.george['id'] + '&type=me&oldest=' + str(int(timestamp)))
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.contemporary_art])

        ## test latest/oldest with me page and extreme cases
        quote = Quote.query.filter_by(content=RandomQuotes.contemporary_art['quote']).first()
        timestamp = time.mktime(quote.created.timetuple()) - 10

        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.george['id'] + '&type=me&latest=' + str(int(timestamp)))
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.contemporary_art, RandomQuotes.girlfriend, RandomQuotes.andanotherone])

        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.george['id'] + '&type=me&oldest=' + str(int(timestamp)))
        rv_list = json.loads(rv.data)
        assert len(rv_list) == 0

        quote = Quote.query.filter_by(content=RandomQuotes.andanotherone['quote']).first()
        timestamp = time.mktime(quote.created.timetuple()) + 10

        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.george['id'] + '&type=me&latest=' + str(int(timestamp)))
        rv_list = json.loads(rv.data)
        assert len(rv_list) == 0

        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.george['id'] + '&type=me&oldest=' + str(int(timestamp)))
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.contemporary_art, RandomQuotes.girlfriend, RandomQuotes.andanotherone])

        ## test limit
        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.george['id'] + '&limit=2')
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.anotherquote, RandomQuotes.andanotherone])

        ## test limit with me page
        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.angela['id'] + '&type=me&limit=2')
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.girlfriend, RandomQuotes.anotherquote])

        ## test limit with latest/oldest
        quote = Quote.query.filter_by(content=RandomQuotes.girlfriend['quote']).first()
        timestamp = time.mktime(quote.created.timetuple())

        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.george['id'] + '&latest=' + str(int(timestamp)) + '&limit=1')
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.andanotherone])

        timestamp += 1 ## relies on the fact that they're 1 second apart (see time.sleep() above)
        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.george['id'] + '&oldest=' + str(int(timestamp)) + '&limit=1')
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.girlfriend])
 
        ## test limit extreme cases
        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.deepika['id'] + '&limit=10')
        rv_list = json.loads(rv.data)
        self.assert_is_same_list_of_quotes(rv_list, [RandomQuotes.contemporary_art, RandomQuotes.girlfriend, RandomQuotes.andanotherone])

        rv = self.app.get('/get_quotes?fbid=' + RandomUsers.deepika['id'] + '&limit=0')
        rv_list = json.loads(rv.data)
        assert len(rv_list) == 0

        print "\n -------end test get quotes --------\n"



if __name__ == '__main__':
    unittest.main()
