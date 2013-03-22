import os
from flask import Flask, request
import json
from sqlalchemy import or_
import time
from sqlalchemy import desc
from pprint import pprint

import model
from model import db
from model import User, Quote, Comment, Favorite, Echo
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
    return format_response(SuccessMessages.FRIENDSHIP_ADDED);

@app.route("/add_user", methods = ['POST'])
def add_user():
    udata = json.loads(request.values.get('data'))
    fbid = udata['id']
    picture_url = udata['picture_url']
    email = udata['email']
    first_name, last_name = split_name(udata['name'])
    friends_raw = udata['friends']

    try:
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
            raise ServerException(ErrorMessages.USER_IS_ALREADY_REGISTERED, \
                ServerException.ER_BAD_USER) # must call update_user instead

        db.session.commit()
        return format_response(SuccessMessages.USER_ADDED)
    except ServerException as e:
        return format_response(None, e)

@app.route("/update_user", methods = ['POST'])
def update_user():
    udata = json.loads(request.values.get('data'))
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

    try:
        user = User.query.filter_by(fbid = fbid).first()
        if not user:
            # user does not exist -- must call add_user
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        elif user.registered == False:
            # user was pre-signed up by a friend but that's the first time she's logging in -- must call add_user
            raise ServerException(ErrorMessages.USER_NOT_REGISTERED, \
                ServerException.ER_BAD_USER)
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
        return format_response(SuccessMessages.USER_UPDATED) 
    except ServerException as e:
        return format_response(None, e)

@app.route("/add_quote", methods = ['POST'])
def add_quote():
    qdata = json.loads(request.values.get('data'))
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

    try:
        source = User.query.filter_by(fbid = sourceFbid).first()
        reporter = User.query.filter_by(fbid = reporterFbid).first()
        if not source:
            raise ServerException(ErrorMessages.SOURCE_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        if not reporter:
            raise ServerException(ErrorMessages.REPORTER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        quote = Quote(source.id, reporter.id, content, location, location_lat, location_long, False)
     
        db.session.add(quote)
        db.session.commit()
        return format_response(SuccessMessages.QUOTE_ADDED)
    except ServerException as e:
        return format_response(None, e)


@app.route("/add_comment", methods = ['POST'])
def add_comment():
    qdata = json.loads(request.values.get('data'))
    quoteId = qdata['quoteId']
    userFbid = qdata['userFbid']
    content = qdata['comment']

    try:
        user = User.query.filter_by(fbid = userFbid).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        comment = Comment(user.id, quote.id, content)
        db.session.add(comment)
        db.session.commit()
        return format_response(SuccessMessages.COMMENT_ADDED)
    except ServerException as e:
        return format_response(None, e)

@app.route("/add_echo", methods = ['POST'])
def add_echo():
    qdata = json.loads(request.values.get('data'))
    quoteId = qdata['quoteId']
    userFbid = qdata['userFbid']

    try:
        user = User.query.filter_by(fbid = userFbid).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        userId = user.id

        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        if user not in quote.echoers:
            quote.echoers.append(user)
        db.session.commit()
        return format_response(SuccessMessages.ECHO_ADDED)
    except ServerException as e:
        return format_response(None, e)

@app.route("/add_fav", methods = ['POST'])
def add_fav():
    qdata = json.loads(request.values.get('data'))
    quoteId = qdata['quoteId']
    userFbid = qdata['userFbid']

    try:
        user = User.query.filter_by(fbid = userFbid).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        userId = user.id

        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        ## see if the favorite is already logged
        favorite = Favorite.query.filter_by(quote_id = quoteId, user_id = userId).first()
        if favorite:
            raise ServerException(ErrorMessages.FAV_ALREADY_EXISTS, \
                ServerException.ER_BAD_FAV)

        favorite = Favorite(quote)
        user.favs.append(favorite)
        db.session.commit()
        return format_response(SuccessMessages.FAV_ADDED)
    except ServerException as e:
        return format_response(None, e)
    

#-------------------------------------------
#           DELETE REQUESTS
#-------------------------------------------


@app.route("/delete_quote/<quoteId>", methods = ['DELETE'])
def delete_quote(quoteId):
    try:
        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        db.session.delete(quote)
        db.session.commit()
        return format_response(SuccessMessages.QUOTE_DELETED)
    except ServerException as e:
        return format_response(None, e)


@app.route("/delete_echo/<quoteId>/<userFbid>", methods = ['DELETE'])
def delete_echo(quoteId, userFbid):
    try:
        user = User.query.filter_by(fbid = userFbid).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        quote.echoers.remove(user)
        db.session.commit()
        return format_response(SuccessMessages.ECHO_DELETED)
    except ServerException as e:
        return format_response(None, e)


@app.route("/delete_friendship/<aFbid>/<bFbid>", methods = ['DELETE'])
def delete_friendship(aFbid, bFbid):
    try:
        userA = User.query.filter_by(fbid = aFbid).first()
        if not userA:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        userB = User.query.filter_by(fbid = bFbid).first()
        if not userB:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        if userB in userA.friends:
            userA.friends.remove(userB)
        if userA in userB.friends:
            userB.friends.remove(userA)
        db.session.commit()
        return format_response(SuccessMessages.FRIENDSHIP_DELETED)
    except ServerException as e:
        return format_response(None, e)


@app.route("/delete_comment/<commentId>", methods = ['DELETE'])
def delete_comment(commentId):
    try:
        comment = Comment.query.filter_by(id = commentId).first()
        if not comment:
            raise ServerException(ErrorMessages.COMMENT_NOT_FOUND, \
                ServerException.ER_BAD_COMMENT)

        db.session.delete(comment)
        db.session.commit()
        return format_response(SuccessMessages.COMMENT_DELETED)
    except ServerException as e:
        return format_response(None, e)


@app.route("/delete_fav/<quoteId>/<userFbid>", methods = ['DELETE'])
def remove_fav(quoteId, userFbid):
    try:
        user = User.query.filter_by(fbid = userFbid).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        userId = user.id

        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        ## see if the favorite is already logged
        favorite = Favorite.query.filter_by(quote_id = quoteId, user_id = userId).first()
        if not favorite:
            raise ServerException(ErrorMessages.FAV_EXISTENTIAL_CRISIS, \
                ServerException.ER_BAD_FAV)

        db.session.delete(favorite)
        db.session.commit()
        return format_response(SuccessMessages.FAV_DELETED) 
    except ServerException as e:
        return format_response(None, e)

     

#-------------------------------------------
#           GET REQUESTS
#-------------------------------------------

def quote_dict_from_obj(quote):
    quote_res = dict()
    quote_res['_id'] = str(quote.id)
    quote_res['timestamp'] = datetime_to_timestamp(quote.created) # doesn't jsonify
    quote_res['sourceFbid'] = quote.source.fbid
    quote_res['reporterFbid'] = quote.reporter.fbid
    quote_res['location'] = quote.location
    quote_res['location_lat'] = quote.location_lat
    quote_res['location_long'] = quote.location_long
    quote_res['quote'] = quote.content
    quote_res['echo_count'] = len(quote.echoers)
    quote_res['fav_count'] = len(quote.favs)
    return quote_res

@app.route("/get_quote", methods = ['get'])
def get_quote():
    quoteId = request.args.get('id')
    userFbid = request.args.get('userFbid')

    try:
        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        user = User.query.filter_by(fbid = userFbid).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        # TODO there is some code duplication with get_quotes below... we should think if it could be avoided
        quote_res = quote_dict_from_obj(quote)

        #check if quote is echo
        ids = [friend.id for friend in user.friends]
        ids.append(user.id)
        quote_res['is_echo'] = 0
        if quote.source_id not in ids and quote.reporter_id not in ids: 
            echo = Echo.query.filter(Echo.user_id.in_(ids)).order_by(Echo.created).first()
            quote_res['timestamp'] = datetime_to_timestamp(echo.created)
            quote_res['is_echo'] = 1
            quote_res['reporterFbid'] = echo.user.fbid

        quote_res['user_did_fav'] = Favorite.query.filter_by(quote_id=quote.id, user_id=user.id).count() > 0
        quote_res['user_did_echo'] = Echo.query.filter_by(quote_id=quote.id, user_id=user.id).count() > 0

        quote_res['comments'] = []
        comments = Comment.query.filter_by(quote_id = quote.id).order_by(Comment.created) # TODO figure out how to do it nicer using quote.comments with an implicit order_by defined as part of the relationship in model.py. Note that without the order_by it stil works b/c it returns them in order of creation, so technically we could still use quote.comments, however that would induce too much coupling between how sqlalchemy works and our code. Check out http://stackoverflow.com/questions/6750251/sqlalchemy-order-by-on-relationship-for-join-table 
        for comment in comments:
            comment_res = dict()
            comment_res['id'] = comment.id
            comment_res['fbid'] = comment.user.fbid
            comment_res['timestamp'] = datetime_to_timestamp(comment.created)
            comment_res['comment'] = comment.content
            comment_res['name'] = comment.user.first_name + ' ' + comment.user.last_name
            comment_res['picture_url'] = comment.user.picture_url
            comment_res['is_friend_or_me'] = comment.user_id in ids
            quote_res['comments'].append(comment_res)

        return format_response(quote_res);
    except ServerException as e:
        return format_response(None, e);

@app.route('/get_quotes_with_ids', methods = ['post'])
def get_quotes_with_ids():
    ids = json.loads(request.values.get('data'))

    result = []
    for id in ids:
        quote = Quote.query.filter_by(id = id).first()
        if not quote:
            result.append(None)
        else:
            result.append(quote_dict_from_obj(quote))

    return format_response(result)

@app.route("/get_quotes", methods = ['get'])
def get_quotes():
    fbid = request.args.get('fbid')
    req_type = request.args.get('type')
    oldest = request.args.get('oldest')
    latest = request.args.get('latest')
    limit = request.args.get('limit')
    if not limit:
        limit = APIConstants.DEFAULT_GET_QUOTES_LIMIT

    try:
        user = User.query.filter_by(fbid = fbid).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        #or_conds = [or_(Quote.sourceId = friend.id, Quote.reporterId = friend.id) for friend in user.friends]
        #or_conds.append(or_(Quote.sourceId = user.id, Quote.reporterId = user.id)) # this is very old -- not sure why I'm still keeping it

        ## construct OR condition for which quotes to pick
        if req_type == 'me':
            ids = []
        else:
            ids = [friend.id for friend in user.friends]
        ids.append(user.id)
        or_conds = or_(Quote.source_id.in_(ids), Quote.reporter_id.in_(ids), Quote.echoers.any(User.id.in_(ids)))

        ## fetch quotes
        if latest:
            created = time.localtime(float(latest))
            created = time.strftime(DatetimeConstants.MYSQL_DATETIME_FORMAT, created)
            quotes = Quote.query.filter(or_conds, Quote.created > created).order_by(desc(Quote.created)).limit(limit).all()
        elif oldest:
            created = time.localtime(float(oldest))
            created = time.strftime(DatetimeConstants.MYSQL_DATETIME_FORMAT, created)
            quotes = Quote.query.filter(or_conds, Quote.created < created).order_by(desc(Quote.created)).limit(limit).all()
        else:
            quotes = Quote.query.filter(or_conds).order_by(desc(Quote.created)).limit(limit).all()

        ## figure out which quotes are echoes
        are_echoes = [0] * len(quotes)
        for i, quote in enumerate(quotes):
            if quote.source_id not in ids and quote.reporter_id not in ids:
                are_echoes[i] = 1
                # TODO is this efficient? Maybe look into some crazy joins later on
                echo = Echo.query.filter(Echo.user_id.in_(ids)).order_by(Echo.created).first()
                if not echo:
                    print 'DAMN there are no echoer friends when they should be!\
                           wtf...... TODO figure out how to handle sublte bugs like this...\
                           can\'t assert and can\'t throw an exception, obviously'
                quote.created = echo.created
                quote.reporter = echo.user
        sorted_quotes = sorted(quotes, key = lambda q: q.created, reverse = True)

        ## convert them to dictionary according to API specs
        result = []
        for i, quote in enumerate(sorted_quotes):
            quote_res = quote_dict_from_obj(quote)
            # TODO is there a better way to do this? e.g. user in quote.fav_users
            # tho it might be a heavier operation behind the scenes
            quote_res['user_did_fav'] = Favorite.query.filter_by(quote_id=quote.id, user_id=user.id).count() > 0
            quote_res['user_did_echo'] = Echo.query.filter_by(quote_id=quote.id, user_id=user.id).count() > 0
            quote_res['is_echo'] = are_echoes[i]
            result.append(quote_res)

        #sorted_result = sorted(result, key = lambda k: k['timestamp'], reverse=True) -- we don't need this anymore, leaving it here for syntax reference on how to sort array of dictionaries
        dump = json.dumps(result)
        return format_response(result)
    except ServerException as e:
        return format_response(None, e)

@app.route("/get_echoers", methods = ['get'])
def get_echoers():
    quoteId = request.args.get('quoteId')

    try:
        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        result = []
        for echoer in quote.echoers:
            echoer_res = {
                'first_name': echoer.first_name,
                'last_name': echoer.last_name,
                'fbid': echoer.fbid
            }
            result.append(echoer_res)

        return format_response(result);
    except ServerException as e:
        return format_response(None, e);

@app.route("/get_favs", methods = ['get'])
def get_favs():
    quoteId = request.args.get('quoteId')

    try:
        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        favs = Favorite.query.filter_by(quote_id = quoteId)
        result = []
        for fav in favs:
            fav_res = {
                'first_name': fav.user.first_name,
                'last_name': fav.user.last_name,
                'fbid': fav.user.fbid
            }
            result.append(fav_res)

        return format_response(result);
    except ServerException as e:
        return format_response(None, e);


#-----------------------------
# RESTful utils
#------------------------------

class ServerException(Exception):
    ER_UNKNOWN     = 0
    ER_BAD_QUOTE   = 1
    ER_BAD_USER    = 2
    ER_BAD_FAV     = 3
    ER_BAD_COMMENT = 4

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
