import os
from flask import Flask, request
import json
from sqlalchemy import or_
import time
from sqlalchemy import desc
from pprint import pprint

import model
from model import db
from model import User, Quote, Comment, Favorite
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


#---------------------------------------
#         POST REQUESTS
#----------------------------------------


def add_friends(user, friends_raw):
    for friend_raw in friends_raw:
        friend_fbid = friend_raw['id']
        friend_first, friend_last = split_name(friend_raw['name'])
        friend_picture_url = friend_raw['picture']['data']['url']

        friend = User.query.filter_by(fbid = friend_fbid).first()
        if not friend:
            friend = User(friend_fbid, None, friend_first, friend_last, friend_picture_url,  None, False)
            db.session.add(friend)
        user.friends.append(friend)

@app.route("/add_user", methods = ['POST'])
def add_user():
    udata = json.loads(request.form['data'])
    fbid = udata['id']
    picture_url = udata['picture_url']
    email = udata['email']
    first_name, last_name = split_name(udata['name'])
    friends_raw = udata['friends']

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
        return ErrorMessages.USER_IS_ALREADY_REGISTERED # must call update_user

    db.session.commit()
    return SuccessMessages.USER_ADDED 

@app.route("/update_user", methods = ['POST'])
def update_user():
    udata = json.loads(request.form['data'])
    picture_url = None
    email = None
    first_name = None
    last_name = None
    friends_raw = None
    fbid = udata['id']
    if 'picture_url' in udata:
        picture_url = udata['picture_url']
    if 'email' in udata:
        email = udata['email']
    if 'name' in udata:
        first_name, last_name = split_name(udata['name'])
    if 'friends' in udata:
        friends_raw = udata['friends']

    user = User.query.filter_by(fbid = fbid).first()
    if not user:
        # user does not exist -- must call add_user
        return ErrorMessages.USER_NOT_FOUND
    elif user.registered == False:
        # user was pre-signed up by a friend but that's the first time she's logging in -- must call add_user
        return ErrorMessages.USER_NOT_REGISTERED
    else:
        if picture_url:
            user.picture_url = picture_url
        if email:
            user.email = email
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if friends_raw:
            add_friends(user, friends_raw) # TODO sep thread? also what if you add the same friendship multiple times?

    db.session.commit()
    return SuccessMessages.USER_UPDATED 


@app.route("/add_quote", methods = ['POST'])
def add_quote():
    qdata = json.loads(request.form['data'])
    sourceFbid = qdata['sourceFbid']
    reporterFbid = qdata['reporterFbid']
    location = qdata['location']
    if 'location_lat' in qdata:
        location_lat = qdata['location_lat']
    else:
        location_lat = None
    if 'location_long' in qdata:
        location_long = qdata['location_long']
    else:
        location_long = None
    content = qdata['quote']

    print ' ADD QUOTE '

    source = User.query.filter_by(fbid = sourceFbid).first()
    reporter = User.query.filter_by(fbid = reporterFbid).first()
    if not source:
        return ErrorMessages.SOURCE_NOT_FOUND 
    if not reporter:
        return ErrorMessages.REPORTER_NOT_FOUND 

    quote = Quote(source.id, reporter.id, content, location, location_lat, location_long, False)
 
    pprint(quote)
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

@app.route("/add_echo", methods = ['POST'])
def add_echo():
    data = json.loads(request.form['data'])
    quoteId = data['quoteId']
    userFbid = data['userFbid']

    user = User.query.filter_by(fbid = userFbid).first()
    if not user:
        return ErrorMessages.USER_NOT_FOUND
    quote = Quote.query.filter_by(id = quoteId).first()
    if not quote:
        return ErrorMessages.QUOTE_NOT_FOUND

    quote.echoers.append(user)
    db.session.commit()
    return SuccessMessages.ECHO_ADDED


#-------------------------------------------
#           DELETE REQUESTS
#-------------------------------------------


@app.route("/delete_quote/<quoteId>", methods = ['DELETE'])
def delete_quote(quoteId):
    quote = Quote.query.filter_by(id = quoteId).first()
    if not quote:
        return ErrorMessages.QUOTE_NOT_FOUND

    db.session.delete(quote)
    db.session.commit()
    return SuccessMessages.QUOTE_DELETED


@app.route("/delete_echo/<quoteId>/<userFbid>", methods = ['DELETE'])
def delete_echo(quoteId, userFbid):
    user = User.query.filter_by(fbid = userFbid).first()
    if not user:
        return ErrorMessages.USER_NOT_FOUND

    quote = Quote.query.filter_by(id = quoteId).first()
    if not quote:
        return ErrorMessages.QUOTE_NOT_FOUND

    quote.echoers.remove(user)
    db.session.commit()
    return SuccessMessages.ECHO_DELETED


@app.route("/delete_friendship/<aFbid>/<bFbid>", methods = ['DELETE'])
def delete_friendship(aFbid, bFbid):
    userA = User.query.filter_by(fbid = aFbid).first()
    if not userA:
        return ErrorMessages.USER_NOT_FOUND
    userB = User.query.filter_by(fbid = bFbid).first()
    if not userB:
        return ErrorMessages.USER_NOT_FOUND

    if userB in userA.friends:
        userA.friends.remove(userB)
    if userA in userB.friends:
        userB.friends.remove(userA)
    db.session.commit()
    return SuccessMessages.FRIENDSHIP_DELETED


@app.route("/delete_comment/<commentId>", methods = ['DELETE'])
def delete_comment(commentId):
    comment = Comment.query.filter_by(id = commentId).first()
    if not comment:
        return ErrorMessages.COMMENT_NOT_FOUND

    db.session.delete(comment)
    db.session.commit()
    return SuccessMessages.COMMENT_DELETED



#-------------------------------------------
#           GET REQUESTS
#-------------------------------------------


@app.route("/add_fav", methods = ['POST'])
def add_fav():
    qdata = json.loads(request.form['data'])
    quoteId = qdata['quoteId']
    userFbid = qdata['fbid']

    user = User.query.filter_by(fbid = userFbid).first()
    if not user:
        return ErrorMessages.USER_NOT_FOUND 
    userId = user.id

    quote = Quote.query.filter_by(id = quoteId).first()
    if not quote:
        return ErrorMessages.QUOTE_NOT_FOUND

    ## see if the favorite is already logged
    favorite = Favorite.query.filter_by(quote_id = quoteId, user_id = userId).first()
    if favorite:
        return ErrorMessages.FAV_ALREADY_EXISTS

    favorite = Favorite(quote)
    user.fav_quotes.append(favorite)

    db.session.commit()
    return SuccessMessages.FAV_ADDED     

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
    quote_res['num_echoes'] = len(quote.echoers)
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

    friends_ids = dict()
    for friend in user.friends:
        friends_ids[friend.id] = 1

    quote_res = quote_dict_from_obj(quote)

    quote_res['comments'] = []
    comments = Comment.query.filter_by(quote_id = quote.id).order_by(Comment.created) # TODO figure out how to do it nicer using quote.comments with an implicit order_by defined as part of the relationship in model.py. Note that without the order_by it stil works b/c it returns them in order of creation, so technically we could still use quote.comments, however that would induce too much coupling between how sqlalchemy works and our code. Check out http://stackoverflow.com/questions/6750251/sqlalchemy-order-by-on-relationship-for-join-table 
    for comment in comments:
        comment_res = dict()
        comment_res['id'] = comment.id
        comment_res['fbid'] = comment.user.fbid
        comment_res['timestamp'] = time.mktime(comment.created.timetuple())
        comment_res['comment'] = comment.content
        if comment.user_id not in friends_ids:
            comment_res['name'] = comment.user.first_name + ' ' + comment.user.last_name
            comment_res['picture_url'] = comment.user.picture_url
        quote_res['comments'].append(comment_res)

    quote_res['num_favs'] = len(quote.fav_users)

    dump = json.dumps(quote_res)
    return dump

@app.route('/get_quotes_with_ids', methods = ['post'])
def get_quotes_with_ids():
    ids = json.loads(request.form['data'])

    result = []
    for id in ids:
        quote = Quote.query.filter_by(id = id).first()
        if not quote:
            result.append(None)
        else:
            result.append(quote_dict_from_obj(quote))

    return json.dumps(result)

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
    or_conds = or_(Quote.source_id.in_(ids), Quote.reporter_id.in_(ids), Quote.echoers.any(User.id.in_(ids)))

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
