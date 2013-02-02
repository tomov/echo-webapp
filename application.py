import os
from flask import Flask, request
import json
from sqlalchemy import or_
import time

import model
from model import db
from model import User, Quote, Echo, Comment
from model import create_db
from constants import *
from util import *

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

#----------------------------------------
# controllers
#----------------------------------------

@app.route("/")
def hello():
    return "Hello from Python yay!"

def add_friends(user, friends_raw):
    for friend_raw in friends_raw:
        friend_fbid = friend_raw['id']
        friend_first, friend_last = split_name(friend_raw['name'])
        friend_picture_url = friend_raw['picture']['data']['url']
        #print 'add friend ' + friend_first + ' ' + friend_last + ' fbid = ' + friend_fbid

        friend = User.query.filter_by(fbid = friend_fbid).first()
        if not friend:
            friend = User(friend_fbid, None, friend_first, friend_last, friend_picture_url,  None, False)
            db.session.add(friend)
        user.friends.append(friend) # no worries, it's stored by reference in new_users_list


@app.route("/add_user", methods = ['POST'])
def add_user():
    udata = json.loads(request.form['data'])
    fbid = udata['id']
    picture_url = udata['picture_url']
    first_name, last_name = split_name(udata['name'])
    friends_raw = udata['friends']
    #print 'add user with name ' + first_name + ' ' + last_name + ' and ' + str(len(friends_raw)) + ' friends'
    #print json.dumps(udata)

    user = User.query.filter_by(fbid = fbid).first()
    if not user:
        # user does not exist -- create one
        user = User(fbid, udata['email'], first_name, last_name, picture_url, None, True)
        add_friends(user, friends_raw)
        db.session.add(user)
    elif user.registered == False:
        # user was pre-signed up by a friend but that's the first time she's logging in
        user.registered = True
        add_friends(user, friends_raw) # TODO sep thread?
    else:
        return ErrorMessages.USER_IS_ALREADY_REGISTERED

    db.session.commit()
    return SuccessMessages.USER_ADDED 
 

@app.route("/add_quote", methods = ['POST'])
def add_quote():
    qdata = json.loads(request.form['data'])
    sourceFbid = qdata['sourceFbid']
    reporterFbid = qdata['reporterFbid']
    location = qdata['location']
    content = qdata['quote']

    source = User.query.filter_by(fbid = sourceFbid).first()
    reporter = User.query.filter_by(fbid = reporterFbid).first()
    if not source:
        return ErrorMessages.SOURCE_NOT_FOUND 
    if not reporter:
        return ErrorMessages.REPORTER_NOT_FOUND 

    quote = Quote(source.id, reporter.id, content, location, False)
    db.session.add(quote)
    db.session.commit()
    return SuccessMessages.QUOTE_ADDED 


@app.route("/add_comment", methods = ['POST'])
def add_comment():
    qdata = json.loads(request.form['data'])
    quoteId = qdata['quoteId']
    userFbid = qdata['userFbid']
    content = qdata['comment']

    user = User.query.filter_by(fbid = userFbid).first()
    quote = Quote.query.filter_by(id = quoteId).first()
    if not user:
        return ErrorMessages.USER_NOT_FOUND 
    if not quote:
        return ErrorMessages.QUOTE_NOT_FOUND

    comment = Comment(user.id, quote.id, content)
    db.session.add(comment)
    db.session.commit()
    return SuccessMessages.COMMENT_ADDED 


@app.route("/get_quote", methods = ['get'])
def get_quote():
    quoteId = request.args.get('id')


    print 'GET QUOTE'
    quote = Quote.query.filter_by(id = quoteId).first()
    if not quote:
        return ErrorMessages.QUOTE_NOT_FOUND

    quote_res = dict()
    quote_res['_id'] = str(quote.id)
    quote_res['timestamp'] = time.mktime(quote.created.timetuple()) # doesn't jsonify
    quote_res['sourceFbid'] = quote.source.fbid
    quote_res['reporterFbid'] = quote.reporter.fbid
    quote_res['location'] = quote.location
    quote_res['quote'] = quote.content

    dump = json.dumps(quote_res)
    return dump


@app.route("/get_quotes", methods = ['get'])
def get_quotes():
    fbid = request.args.get('fbid')
    req_type = request.args.get('type')
    oldest = request.args.get('oldest')
    latest = request.args.get('latest')

    user = User.query.filter_by(fbid = fbid).first()
    if not user:
        return ErrorMessages.USER_NOT_FOUND

    #or_conds = [or_(Quote.sourceId = friend.id, Quote.reporterId = friend.id) for friend in user.friends]
    #or_conds.append(or_(Quote.sourceId = user.id, Quote.reporterId = user.id))
   
    if req_type == 'me':
        ids = []
    else:
        ids = [friend.id for friend in user.friends]
    ids.append(user.id)

    if latest:
        created = time.localtime(float(latest))
        created = time.strftime(DatetimeConstants.MYSQL_DATETIME_FORMAT, created)
        quotes = Quote.query.filter(or_(Quote.source_id.in_(ids), Quote.reporter_id.in_(ids)), Quote.created > created).all()
    elif oldest:
        created = time.localtime(float(oldest))
        created = time.strftime(DatetimeConstants.MYSQL_DATETIME_FORMAT, created)
        quotes = Quote.query.filter(or_(Quote.source_id.in_(ids), Quote.reporter_id.in_(ids)), Quote.created < created).all()
    else:
        quotes = Quote.query.filter(or_(Quote.source_id.in_(ids), Quote.reporter_id.in_(ids))).all()

    result = []
    for quote in quotes:
        # TODO (mom/rishi) coordinate field type and naming convention
        quote_res = dict()
        quote_res['_id'] = str(quote.id)
        quote_res['timestamp'] = time.mktime(quote.created.timetuple()) # doesn't jsonify
        quote_res['sourceFbid'] = quote.source.fbid
        quote_res['reporterFbid'] = quote.reporter.fbid
        quote_res['location'] = quote.location
        quote_res['quote'] = quote.content
        result.append(quote_res)

    sorted_result = sorted(result, key = lambda k: k['timestamp'], reverse=True)
    #print sorted_result
    dump = json.dumps(sorted_result)
    return dump


#----------------------------------------
# launch
#----------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True) # TODO (mom) remove debug before release
