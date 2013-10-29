import os
import sys
import unittest
from sqlalchemy import desc
from flask.ext.sqlalchemy import SQLAlchemy

sys.path.append('..') # hack to be able to import files from parent directory without messing with modules
import application
import model
from model import db
from model import User, Quote
from constants import *
from util import *
from mock_data import *

# DO NOT TOUCH THIS!!!!! If you do, you might fuck up the real db, and Momchil will personally come find you and behead you in your sleep
TEST_DATABASE_NAME = 'echo_webapp_test' # DO NOT FUCK THIS UP! or you'll erase the real db....
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

        MockUserData.static__init__() # initialize mock user data

    def tearDown(self): #: called after the test is run (close shit)
        db.session.remove() # REALLY IMPORTANT to do this before the one below, otherwise can't run more than one test
        db.drop_all() #: get rid of tables
        print '===> teardown: end'
