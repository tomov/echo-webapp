# -*- coding: utf-8 -*-

import os
from flask import Flask, request, render_template
import json
from sqlalchemy import or_, and_
import time
from sqlalchemy import desc
from pprint import pprint
from sets import Set
import datetime

# api
from user_api import *
from quote_api import *
from comment_api import *
from fav_api import *
from echo_api import *
from notif_api import *
from misc_api import *

# db model
import model
from model import db
from model import User, Quote, Comment, Favorite, Echo, Feedback, Access_Token, Notification, NotifPrefs, APIEvent
from model import create_db

# misc
from constants import *
from util import *
from fb_og import *

# for auth
import urllib
import urllib2
import tokenlib
import random

# for push notifications
from apns import APNs, Payload

#----------------------------------------
# Decorator
#----------------------------------------

# to be used as a decorator -- must return a callable
from functools import wraps
def authenticate(func):
    @wraps(func)
    def decorated_function(user_id="", access_token="", *args, **kwargs):
        try:
            authorize_user(user_id, access_token)
        except AuthException as e:
            return format_response(None, e)
        return func(*args, **kwargs)
    return decorated_function

#----------------------------------------
# initialization
#----------------------------------------

application = Flask(__name__)  # Amazon Beanstalk bs
app = application              # ...and a hack around it

app.config.update(
    DEBUG = True,  # TODO (mom) remove before deploying
)

app.config['SQLALCHEMY_DATABASE_URI'] = DatabaseConstants.DATABASE_URI 
db.init_app(app)

# used for auth - 1 year = 31560000, 1 month = ?, 
manager = tokenlib.TokenManager(secret="sL/mZPxS:]CI)@OWpP!GR9![a.&{i)i", timeout=7776000)

#----------------------------------------
# controllers
#----------------------------------------

@app.route("/")
def hello():
    create_db()
    return "Hello from Python yay!"

#---------------------------------------
#         Helper functions
#----------------------------------------


def track_event(user_id, name):
    event = APIEvent.query.filter_by(user_id=user_id, name=name).first()
    if event:
        event.count = event.count + 1
    else:
        event = APIEvent(user_id, name)
        db.session.add(event)
    db.session.commit()


#-----------------------------
# RESTful utils
#------------------------------

class ServerException(Exception):
    ER_UNKNOWN     = 0
    ER_BAD_QUOTE   = 1
    ER_BAD_USER    = 2
    ER_BAD_FAV     = 3
    ER_BAD_COMMENT = 4
    ER_BAD_PARAMS  = 5
    ER_BAD_ECHO    = 6

    def __init__(self, message, n=ER_UNKNOWN):
        self.message = message
        self.n = n

    def to_dict(self):
        return {'errno' : self.n, 'message' : self.message}

    def __str__(self):
        return "[%d] %s" % self.message

def format_response(ret=None, error=None):
    if ret is None:
        ret = {}
    elif isinstance(ret, basestring):
        ret = {'message' : ret}
    if error:
        #assert isinstance(error, ServerException)
        ret['error'] = error.to_dict() 
    return json.dumps(ret)



#---------------------------------------
#  shit
#---------------------------------------

#this is for the Test UI, otherwise Chrome blocks cross-site referencing by javascript
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'DELETE, POST, GET, PUT, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept')
    return response

#----------------------------------------
# launch
#----------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True) # TODO (mom) remove debug before release
