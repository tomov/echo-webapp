import os
import application
import unittest
import tempfile
from model import db
from model import User, Quote, Echo, Comment
import json

from flask.ext.sqlalchemy import SQLAlchemy

#: these lines will be used throughout for debugging purposes
print '===> _before: using db -- ' + application.app.config['SQLALCHEMY_DATABASE_URI']

class ApplicationTestCase(unittest.TestCase):


    def setUp(self): #: called before each individual test function is run
        ''' Uncomment this to use a tempfile for db
        self.db_fd, application.app.config['DATABASE'] = tempfile.mkstemp()
        application.app.config['TESTING'] = True

        application.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + application.app.config['DATABASE']
        '''

        application.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db' #: use sqlite db for testing

        print '===> setup: using db -- ' + application.app.config['SQLALCHEMY_DATABASE_URI']

        db.app = application.app
        db.create_all() #: initialize all tables

        self.app = application.app.test_client()

    def tearDown(self): #: called after the test is run (close shit)
        # os.close(self.db_fd)
        # os.unlink(application.app.config['DATABASE'])
        
        db.drop_all(app=application.app) #: get rid of tables

        print '===> teardown: end'

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

# ----------------------------------------------------------------------
# Tests. Note: test functions must begin with "test" i.e. test_something
# ----------------------------------------------------------------------

    def test_empty_db(self):
        print '===> test_empty_db: start'

        assert len(Quote.query.all()) == 0
        assert len(User.query.all()) == 0
        assert len(Echo.query.all()) == 0
        assert len(Comment.query.all()) == 0

        print '===> test_empty_db: end'

    def test_add_quote(self):
        print '===> test_add_quote: start'

        self.add_sample_data()
        assert len(User.query.all()) != 0

        #: test add_quote
        quote = {
                'sourceFbid' : 1,
                'reporterFbid' : 2,
                'location' : 'Princeton, NJ',
                'quote' : 'Testing add_quote.'
        } 
        dump = json.dumps(quote)
        
        rv = self.app.post('/add_quote', data=dict(data=dump))

        find_quote = Quote.query.filter_by(content='Testing add_quote.').first()
        assert find_quote is not None

        # make sure source and reporter exist
        source = User.query.filter_by(fbid=quote['sourceFbid']).first()
        reporter = User.query.filter_by(fbid=quote['reporterFbid']).first()
        assert source is not None
        assert reporter is not None

        # test invalid quotes
        invalid_quote = {
                        'sourceFbid' : 0, #: invalid
                        'reporterFbid' : 1,
                        'location' : 'Princeton, NJ',
                        'quote' : 'Source DNE.'
        }
        dump = json.dumps(invalid_quote)
        rv = self.app.post('/add_quote', data=dict(data=dump))

        find_invalid_quote = Quote.query.filter_by(content='Source DNE.').first()
        assert find_invalid_quote is None

        invalid_quote = {
                        'sourceFbid' : 1,
                        'reporterFbid' : 0, #: invalid
                        'location' : 'Princeton, NJ',
                        'quote' : 'Reporter DNE.'
        }
        dump = json.dumps(invalid_quote)
        rv = self.app.post('/add_quote', data=dict(data=dump))

        find_invalid_quote = Quote.query.filter_by(content='Reporter DNE.').first()
        assert find_invalid_quote is None

        #: TODO sql-injections (content)

        print '===> test_add_quote: end'

    def test_get_quotes(self):
        print '===> test_get_quotes: start'

        rv = self.app.get('/get_quotes')
        assert 'User NOT signed up' in rv.data

        self.add_sample_data()

        rv = self.app.get('/get_quotes?fbid=1')
        rv_list = json.loads(rv.data)
        assert len(rv_list) == 3

        rv = self.app.get('/get_quotes?fbid=2')
        rv_list = json.loads(rv.data)
        assert len(rv_list) == 3

        rv = self.app.get('/get_quotes?fbid=3')
        rv_list = json.loads(rv.data)
        assert len(rv_list) == 3

        print '===> test_get_quotes: end'

    def test_add_user(self):
        print '===> test_add_user: start'

        self.add_sample_data()
        assert len(User.query.all()) == 3

        user = {
               'id' : 4,
               'email': 'user4@somesite.com',
               'name': 'User Four',
               'friends' : {} # TODO: add friends (already existing and nonexisting)
        }
        dump = json.dumps(user)
        rv = self.app.post('/add_user', data=dict(data=dump))

        find_user = User.query.filter_by(fbid=4).all()
        assert len(find_user) == 1 #: verify that user was added
        
        find_user = find_user[0]

        #: make sure name was split correctly. TODO: how does app handle multiple names?
        assert find_user.first_name == 'User'
        assert find_user.last_name == 'Four'
        
        #: TODO: test for sql injections, insertion of invalid users, duplicates, etc.

        print '===> test_add_user: end'


if __name__ == '__main__':
    unittest.main()
