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
from user_api import user_api
from quote_api import quote_api
from comment_api import comment_api
from fav_api import fav_api
from echo_api import echo_api
from notif_api import notif_api
from misc_api import misc_api

# db model
import model
from model import db
from model import User, Quote, Comment, Favorite, Echo, Feedback, Access_Token, Notification, NotifPrefs, APIEvent
from model import create_db

# misc
from constants import *
from util import *

# for push notifications
from apns import APNs, Payload

#----------------------------------------
# Decorator
#----------------------------------------

#----------------------------------------
# initialization
#----------------------------------------

application = Flask(__name__)  # register application. Must be named application b/c Amazon beanstalk is special
app = application              # hack to make application more conventional

# "include" api methods
app.register_blueprint(user_api)
app.register_blueprint(quote_api)
app.register_blueprint(comment_api)
app.register_blueprint(fav_api)
app.register_blueprint(echo_api)
app.register_blueprint(notif_api)
app.register_blueprint(misc_api)

app.config.update(
    DEBUG = True,  # TODO (mom) remove before deploying
)

app.config['SQLALCHEMY_DATABASE_URI'] = DatabaseConstants.DATABASE_URI 
db.init_app(app)


#----------------------------------------
# controllers
#----------------------------------------

@app.route("/")
def hello():
    create_db()
    return "Hello from Python yay!"

# this is for the Test UI, otherwise Chrome blocks cross-site referencing by javascript
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
