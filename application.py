import os
from flask import Flask, request
import json
from sqlalchemy import or_
import time
from sqlalchemy import desc
from pprint import pprint

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
    email = udata['email']
    first_name, last_name = split_name(udata['name'])
    friends_raw = udata['friends']
    #print 'add user with name ' + first_name + ' ' + last_name + ' and ' + str(len(friends_raw)) + ' friends'
    #print json.dumps(udata)

    user = User.query.filter_by(fbid = fbid).first()
    if not user:
        # user does not exist -- create one
        user = User(fbid, email, first_name, last_name, picture_url, None, True)
        add_friends(user, friends_raw)
        db.session.add(user)
    elif user.registered == False:
        # user was pre-signed up by a friend but that's the first time she's logging in
        user.registered = True
        user.email = email
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
    location_lat = qdata['location_lat']
    location_long = qdata['location_long']
    content = qdata['quote']

    source = User.query.filter_by(fbid = sourceFbid).first()
    reporter = User.query.filter_by(fbid = reporterFbid).first()
    if not source:
        return ErrorMessages.SOURCE_NOT_FOUND 
    if not reporter:
        return ErrorMessages.REPORTER_NOT_FOUND 

    quote = Quote(source.id, reporter.id, content, location, location_lat, location_long, False)
 
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
    if not user:
        return ErrorMessages.USER_NOT_FOUND 
    quote = Quote.query.filter_by(id = quoteId).first()
    if not quote:
        return ErrorMessages.QUOTE_NOT_FOUND

    comment = Comment(user.id, quote.id, content)
    db.session.add(comment)
    db.session.commit()
    return SuccessMessages.COMMENT_ADDED 

def quote_dict_from_obj(quote):
    quote_res = dict()
    quote_res['_id'] = str(quote.id)
    quote_res['timestamp'] = time.mktime(quote.created.timetuple()) # doesn't jsonify
    quote_res['sourceFbid'] = quote.source.fbid
    quote_res['reporterFbid'] = quote.reporter.fbid
    quote_res['location'] = quote.location
    quote_res['location_lat'] = quote.location_lat
    quote_res['location_long'] = quote.location_long
    quote_res['quote'] = quote.content
    return quote_res

@app.route("/get_quote", methods = ['get'])
def get_quote():
    quoteId = request.args.get('id')
    userFbid = request.args.get('userFbid')

    quote = Quote.query.filter_by(id = quoteId).first()
    if not quote:
        return ErrorMessages.QUOTE_NOT_FOUND

    user = User.query.filter_by(fbid = userFbid).first()
    if not user:
        return ErrorMessages.USER_NOT_FOUND
    friends_fbids = dict()
    for friend in user.friends:
        friends_fbids[friend.id] = 1

    quote_res = quote_dict_from_obj(quote)

    quote_res['comments'] = []
    comments = Comment.query.filter_by(quote_id = quote.id).order_by(Comment.created) # TODO figure out how to do it nicer using quote.comments with an implicit order_by defined as part of the relationship in model.py. Note that without the order_by it stil works b/c it returns them in order of creation, so technically we could still use quote.comments, however that would induce too much coupling between how sqlalchemy works and our code. Check out http://stackoverflow.com/questions/6750251/sqlalchemy-order-by-on-relationship-for-join-table 
    for comment in comments:
        comment_res = dict()
        comment_res['id'] = comment.id
        comment_res['fbid'] = comment.user.fbid
        comment_res['timestamp'] = time.mktime(comment.created.timetuple())
        comment_res['comment'] = comment.content
        if comment.user_id not in friends_fbids:
            comment_res['name'] = comment.user.first_name + ' ' + comment.user.last_name
            comment_res['picture_url'] = comment.user.picture_url
        quote_res['comments'].append(comment_res)

    dump = json.dumps(quote_res)
    return dump


@app.route("/get_quotes", methods = ['get'])
def get_quotes():
    fbid = request.args.get('fbid')
    req_type = request.args.get('type')
    oldest = request.args.get('oldest')
    latest = request.args.get('latest')
    limit = request.args.get('limit')
    if not limit:
        limit = APIConstants.DEFAULT_GET_QUOTES_LIMIT

    user = User.query.filter_by(fbid = fbid).first()
    if not user:
        return ErrorMessages.USER_NOT_FOUND

    #or_conds = [or_(Quote.sourceId = friend.id, Quote.reporterId = friend.id) for friend in user.friends]
    #or_conds.append(or_(Quote.sourceId = user.id, Quote.reporterId = user.id)) # this is very old -- not sure why I'm still keeping it
   
    if req_type == 'me':
        ids = []
    else:
        ids = [friend.id for friend in user.friends]
    ids.append(user.id)
    or_conds = or_(Quote.source_id.in_(ids), Quote.reporter_id.in_(ids));

    if latest:
        created = time.localtime(float(latest))
        created = time.strftime(DatetimeConstants.MYSQL_DATETIME_FORMAT, created)
        quotes = Quote.query.filter(or_conds, Quote.created > created).order_by(desc(Quote.created)).limit(limit)
    elif oldest:
        created = time.localtime(float(oldest))
        created = time.strftime(DatetimeConstants.MYSQL_DATETIME_FORMAT, created)
        quotes = Quote.query.filter(or_conds, Quote.created < created).order_by(desc(Quote.created)).limit(limit)
    else:
        quotes = Quote.query.filter(or_conds).order_by(desc(Quote.created)).limit(limit)

    result = []
    for quote in quotes:
        quote_res = quote_dict_from_obj(quote)
        result.append(quote_res)

    #sorted_result = sorted(result, key = lambda k: k['timestamp'], reverse=True) -- we don't need this anymore, leaving it here for syntax reference on how to sort array of dictionaries
    dump = json.dumps(result)
    return dump


#----------------------------------------
# launch
#----------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True) # TODO (mom) remove debug before release
