import os
from flask import Flask, request
import json
from sqlalchemy import or_, and_
import time
from sqlalchemy import desc
from pprint import pprint
from sets import Set

import model
from model import db
from model import User, Quote, Comment, Favorite, Echo, Feedback, Access_Token, Notification
from model import create_db
from constants import *
from util import *

# for auth
import urllib
import urllib2
import tokenlib
import random

# for push notifications
from apns import APNs, Payload

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

# open persistent connection to gateway (and feedback) server for push notifications
apns = APNs(use_sandbox=True, cert_file='certificates/EchoAPNDevCert.pem', key_file='certificates/EchoAPNDevKey.pem')

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

# since we consolidated echoes and quotes in one table -- echoes -- so the client now only knows echo.id's and doesn't know any quote.id's
# so every time she passes a quoteId, it is in fact an echoId and we have to convert it
def get_quote_id_from_echo_id(echo_id):
    echo = Echo.query.filter_by(id=echo_id).first()
    if not echo:
        return None
    return echo.quote_id

def get_echo_id_from_quote_id(quote_id):
    quote = Quote.query.filter_by(id=quote_id).first()
    if not quote or quote.deleted:
        return None
    echo = Echo.query.filter_by(quote_id=quote.id, user_id=quote.reporter_id).first()
    if not echo:
        return None
    return echo.id

#---------------------------------------
#         POST REQUESTS
#----------------------------------------

# note that we don't db.session.commit -- the caller must do that after
def add_friends(user, friends_raw):
    for friend_raw in friends_raw:
        friend_fbid = friend_raw['id']
        friend_first, friend_last = split_name(friend_raw['name'])
        friend_picture_url = friend_raw['picture']['data']['url']

        friend = User.query.filter_by(fbid = friend_fbid).first()
        if not friend:
            # add hollow profile if friend not exists
            friend = User(friend_fbid, None, friend_first, friend_last, friend_picture_url,  None, False)
            db.session.add(friend)
        else: 
            # if exists, update picture url
            friend.picture_url = friend_picture_url
        if friend not in user.friends:
            user.friends.append(friend)

# note that we don't db.session.commit -- the caller must do that after
def remove_friends(user, unfriends_raw):
    if not unfriends_raw:
        return
    for friend_fbid in unfriends_raw:
        friend = User.query.filter_by(fbid = friend_fbid).first()
        if not friend:
            continue
        if friend in user.friends:
            user.friends.remove(friend)

# also functions as update_user
@app.route("/add_user", methods = ['POST'])
def add_user():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

    udata = json.loads(request.values.get('data'))
    fbid = udata['id']
    picture_url = udata['picture_url']
    email = udata['email']
    first_name, last_name = split_name(udata['name'])
    friends_raw = udata['friends']
    unfriends_raw = None
    if 'unfriends' in udata:
        unfriends_raw = udata['unfriends']

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
            add_friends(user, friends_raw)
            remove_friends(user, unfriends_raw)
        else:
            # same as update_user
            user.picture_url = picture_url
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            add_friends(user, friends_raw)
            remove_friends(user, unfriends_raw)

        db.session.commit()
        return format_response(SuccessMessages.USER_ADDED)
    except ServerException as e:
        return format_response(None, e)

# TODO deprecated for now... we use add_user
@app.route("/update_user", methods = ['POST'])
def update_user():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

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
                add_friends(user, friends_raw)

        db.session.commit()
        return format_response(SuccessMessages.USER_UPDATED) 
    except ServerException as e:
        return format_response(None, e)

# note that we don't db.session.commit -- the caller must do that after
def add_notification(user, quote, type, recipient_id):

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

    print 'ADD NOTIFICATION from user ' + str(user.id) + ' quote ' + str(quote.id) + ' type ' + str(type) + ' for recipient ' + str(recipient_id)
    # add notification to db
    notification = Notification(user, quote, type)
    recipient = User.query.filter_by(id=recipient_id).first()
    if not recipient:
        return
    if recipient not in user.friends:
        return
    notification.recipients.append(recipient)
    db.session.add(notification)
    # send push notification to device
    formatted_text = notification_to_text(notification)
    token_hex = recipient.device_token
    if not token_hex:
        return
    print 'send text ' + formatted_text['text']
    #try:
        #payload = Payload(alert=formatted_text['text'], sound="default", badge=0)
        #apns.gateway_server.send_notification(token_hex, payload)
    #except Exception as e:
        #raise  # TODO FIXME this is for debugging purposes only -- remove after testing!
    #    return False
    return

@app.route("/add_quote", methods = ['POST'])
def add_quote():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

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

        if content[-1:] != '.':
            content += '.'
        quote = Quote(source.id, reporter.id, content, location, location_lat, location_long, False)
        # add the reporter as the first "echoer"
        # this creates a dummy entry in the echoes table that corresponds to the original quote, with echo.user_id == quote.reporter_id
        # this makes it easier to fetch quotes and echoes chronologically in get_quotes
        quote.echoers.append(reporter)
        db.session.add(quote)
        db.session.flush() # so we can get quote id

        add_notification(reporter, quote, 'quote', source.id)
        db.session.commit()
        return format_response(SuccessMessages.QUOTE_ADDED)
    except ServerException as e:
        return format_response(None, e)


@app.route("/add_comment", methods = ['POST'])
def add_comment():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

    qdata = json.loads(request.values.get('data'))
    quoteId = get_quote_id_from_echo_id(qdata['quoteId'])
    userFbid = qdata['userFbid']
    content = qdata['comment']

    try:
        user = User.query.filter_by(fbid = userFbid).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote or quote.deleted:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        comment = Comment(user.id, quote.id, content)
        db.session.add(comment)

        if user.id != quote.reporter_id:
            add_notification(user, quote, 'comment', quote.reporter_id)
        if user.id != quote.source_id:
            add_notification(user, quote, 'comment', quote.source_id)
        db.session.commit()
        return format_response(SuccessMessages.COMMENT_ADDED)
    except ServerException as e:
        return format_response(None, e)

@app.route("/add_echo", methods = ['POST'])
def add_echo():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

    qdata = json.loads(request.values.get('data'))
    quoteId = get_quote_id_from_echo_id(qdata['quoteId'])
    userFbid = qdata['userFbid']

    try:
        user = User.query.filter_by(fbid = userFbid).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote or quote.deleted:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        if user not in quote.echoers and user != quote.reporter and user != quote.source:
            quote.echoers.append(user)
            add_notification(user, quote, 'echo', quote.reporter_id)
            add_notification(user, quote, 'echo', quote.source_id)
        db.session.commit()
        return format_response(SuccessMessages.ECHO_ADDED)
    except ServerException as e:
        return format_response(None, e)

@app.route("/add_fav", methods = ['POST'])
def add_fav():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

    qdata = json.loads(request.values.get('data'))
    quoteId = get_quote_id_from_echo_id(qdata['quoteId'])
    userFbid = qdata['userFbid']

    try:
        user = User.query.filter_by(fbid = userFbid).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        userId = user.id

        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote or quote.deleted:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        ## see if the favorite is already logged
        favorite = Favorite.query.filter_by(quote_id = quoteId, user_id = userId).first()
        if favorite:
            raise ServerException(ErrorMessages.FAV_ALREADY_EXISTS, \
                ServerException.ER_BAD_FAV)

        favorite = Favorite(quote)
        user.favs.append(favorite)

        if user.id != quote.reporter_id:
            add_notification(user, quote, 'fav', quote.reporter_id)
        if user.id != quote.source_id:
            add_notification(user, quote, 'fav', quote.source_id)
        db.session.commit()
        return format_response(SuccessMessages.FAV_ADDED)
    except ServerException as e:
        return format_response(None, e)
    
@app.route("/register_token", methods = ['POST'])
def register_token():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

    qdata = json.loads(request.values.get('data'))
    userFbid = qdata['fbid']
    userDeviceToken = qdata['token']

    print userDeviceToken

    try:
        user = User.query.filter_by(fbid = userFbid).first()
        if not user:
            raise ServerException(ErrorMessage.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        if userDeviceToken:
            user.device_token = userDeviceToken
        else:
            user.device_token = None

        db.session.commit()
        return format_response(SuccessMessages.TOKEN_REGISTERED)

    except ServerException as e:
        return format_response(None, e)
    

@app.route('/add_feedback', methods = ['POST'])
def add_feedback():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

    data = json.loads(request.values.get('data'))
    userFbid = data['userFbid']
    content = data['content']
   
    print 'feedback'
    print userFbid
    print content
    
    try:
        user = User.query.filter_by(fbid = userFbid).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        userId = user.id

        print userId
        print content

        feedback = Feedback(userId, content)
        db.session.add(feedback)
        db.session.commit()
        return format_response(SuccessMessages.FEEDBACK_ADDED)
    except ServerException as e:
        return format_response(None, e)

#-------------------------------------------
#           DELETE REQUESTS
#-------------------------------------------


@app.route("/delete_quote/<quoteId>", methods = ['DELETE'])
def delete_quote(quoteId):

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

    try:
        quoteId = get_quote_id_from_echo_id(quoteId)
        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote or quote.deleted:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)
        quote.deleted = True
        db.session.commit()
        return format_response(SuccessMessages.QUOTE_DELETED)
    except ServerException as e:
        return format_response(None, e)


@app.route("/delete_echo/<quoteId>/<userFbid>", methods = ['DELETE'])
def delete_echo(quoteId, userFbid):

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

    try:
        quoteId = get_quote_id_from_echo_id(quoteId)
        user = User.query.filter_by(fbid = userFbid).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote or quote.deleted:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        if user in quote.echoers and user != quote.reporter and user != quote.source:
            quote.echoers.remove(user)
        db.session.commit()
        return format_response(SuccessMessages.ECHO_DELETED)
    except ServerException as e:
        return format_response(None, e)


@app.route("/delete_friendship/<aFbid>/<bFbid>", methods = ['DELETE'])
def delete_friendship(aFbid, bFbid):

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

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

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

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

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

    try:
        user = User.query.filter_by(fbid = userFbid).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        userId = user.id

        quoteId = get_quote_id_from_echo_id(quoteId)
        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote or quote.deleted:
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
    quote_res['_id'] = str(get_echo_id_from_quote_id(quote.id))
    quote_res['source_name'] = quote.source.first_name + ' ' + quote.source.last_name
    quote_res['source_picture_url'] = quote.source.picture_url
    quote_res['reporter_name'] = quote.reporter.first_name + ' ' + quote.reporter.last_name
    quote_res['reporter_picture_url'] = quote.reporter.picture_url
    quote_res['timestamp'] = datetime_to_timestamp(quote.created) # doesn't jsonify
    quote_res['sourceFbid'] = quote.source.fbid
    quote_res['reporterFbid'] = quote.reporter.fbid
    quote_res['location'] = quote.location
    quote_res['location_lat'] = quote.location_lat
    quote_res['location_long'] = quote.location_long
    quote_res['quote'] = quote.content
    quote_res['echo_count'] = len(quote.echoers) - 1   # subtract the dummy echo where echo.user_id == quote.reporter_id
    quote_res['fav_count'] = len(quote.favs)
    return quote_res

@app.route("/get_quote", methods = ['get'])
def get_quote():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

    quoteId = get_quote_id_from_echo_id(request.args.get('id'))
    userFbid = request.args.get('userFbid')

    try:
        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote or quote.deleted:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        user = User.query.filter_by(fbid = userFbid).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        # TODO there is some code duplication with get_quotes below... we should think if it could be avoided
        quote_res = quote_dict_from_obj(quote)
 
        # check if quote is echo
        ids = [friend.id for friend in user.friends]
        ids.append(user.id)
        quote_res['is_echo'] = 0
        if quote.source_id not in ids and quote.reporter_id not in ids: 
            echo = Echo.query.filter(Echo.user_id.in_(ids)).order_by(Echo.id).first()
            quote_res['timestamp'] = datetime_to_timestamp(echo.created)
            quote_res['is_echo'] = 1
            quote_res['reporterFbid'] = echo.user.fbid

        quote_res['user_did_fav'] = Favorite.query.filter_by(quote_id=quote.id, user_id=user.id).count() > 0
        quote_res['user_did_echo'] = user.id != quote.reporter_id and Echo.query.filter_by(quote_id=quote.id, user_id=user.id).count() > 0

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

# TODO maybe deprecate get_quotes_with_ids? this is basically the same thing
@app.route('/check_deleted_quotes', methods = ['post'])
def check_deleted_quotes():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

    ids = json.loads(request.values.get('data'))

    result = []
    for id in ids:
        id = get_quote_id_from_echo_id(id)
        quote = Quote.query.filter_by(id = id).first()
        if not quote or quote.deleted:
            result.append(None)
        else:
            echo_id = get_echo_id_from_quote_id(id)
            result.append({'_id': echo_id})

    return format_response(result)

@app.route('/get_quotes_with_ids', methods = ['post'])
def get_quotes_with_ids():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

    ids = json.loads(request.values.get('data'))

    result = []
    for id in ids:
        id = get_quote_id_from_echo_id(id)
        quote = Quote.query.filter_by(id = id).first()
        if not quote or quote.deleted:
            result.append(None)
        else:
            result.append(quote_dict_from_obj(quote))

    return format_response(result)


@app.route("/get_quotes", methods = ['get'])
def get_quotes():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

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
        or_conds = or_(Echo.quote.has(Quote.source_id.in_(ids)), Echo.quote.has(Quote.reporter_id.in_(ids)), Echo.user_id.in_(ids))

        ## fetch quotes
        ## note that we're using the echo table as a reference to quotes, even for original ones. We're not querying the quotes table
        ## this is so we have to deal with only one id's sequence (the one for echoes) rather than two
        if latest and oldest:
            upper = int(latest)
            lower = int(oldest) 
            if lower > upper:
                lower, upper = upper, lower
            echoes = Echo.query.filter(or_conds, Echo.id >= lower, Echo.id <= upper, Echo.quote.has(Quote.deleted == False)).order_by(desc(Echo.id)).limit(limit).all()
        elif latest:
            lower = int(latest) 
            echoes = Echo.query.filter(or_conds, Echo.id > lower, Echo.quote.has(Quote.deleted == False)).order_by(desc(Echo.id)).limit(limit).all()
        elif oldest:
            upper = int(oldest)
            echoes = Echo.query.filter(or_conds, Echo.id < upper, Echo.quote.has(Quote.deleted == False)).order_by(desc(Echo.id)).limit(limit).all()
        else:
            echoes = Echo.query.filter(or_conds, Echo.quote.has(Quote.deleted == False)).order_by(desc(Echo.id)).limit(limit).all()

        # convert them to dictionary according to API specs
        # also remove duplicates -- only leave the oldest version of each quote that the user has seen.
        # note that for that purpose, we have the results in increasing order of id's, and we have to reverse it at the end
        seen_quote_ids = Set()
        result = []
        for echo in reversed(echoes):
            quote = echo.quote
            if quote.id in seen_quote_ids:
                continue
            seen_quote_ids.add(quote.id)
            # the echo corresponds to the original quote iff echo.user_id == quote.reporter_id
            is_echo = echo.user_id != quote.reporter_id
            if is_echo:
                quote.created = echo.created
                quote.reporter = echo.user
            quote_res = quote_dict_from_obj(quote)
            # TODO is there a better way to do this? e.g. user in quote.fav_users
            # tho it might be a heavier operation behind the scenes
            quote_res['user_did_fav'] = Favorite.query.filter_by(quote_id=quote.id, user_id=user.id).count() > 0
            quote_res['user_did_echo'] = user.id != quote.reporter_id and Echo.query.filter_by(quote_id=quote.id, user_id=user.id).count() > 0
            quote_res['is_echo'] = is_echo
            result.append(quote_res)
        result.reverse()

        #sorted_result = sorted(result, key = lambda k: k['timestamp'], reverse=True) -- we don't need this anymore, leaving it here for syntax reference on how to sort array of dictionaries
        dump = json.dumps(result)
        return format_response(result)
    except ServerException as e:
        return format_response(None, e)

@app.route("/get_echoers", methods = ['get'])
def get_echoers():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

    quoteId = get_quote_id_from_echo_id(request.args.get('quoteId'))

    try:
        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote or quote.deleted:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        result = []
        for echoer in quote.echoers:
            if echoer.id == quote.reporter_id:
                continue
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

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

    quoteId = get_quote_id_from_echo_id(request.args.get('quoteId'))

    try:
        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote or quote.deleted:
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

def notification_to_text(notification):
    user = notification.user
    quote = notification.quote
    if notification.type == 'quote':
        return {
            'text': "{0} {1} posted a quote by you: \"{2}\"".format(user.first_name, user.last_name, quote.content),
            'bold': [{
                    'location': 0,
                    'length': len(user.first_name) + len(user.last_name) + 1
                }]
        }
    elif notification.type == 'echo':
        return {
            'text': "{0} {1} echoed your quote: \"{2}\"".format(user.first_name, user.last_name, quote.content),
            'bold': [{
                    'location': 0,
                    'length': len(user.first_name) + len(user.last_name) + 1
                }]
        }
    elif notification.type == 'comment':
        return {
            'text': "{0} {1} commented on your quote.".format(user.first_name, user.last_name, quote.content),
            'bold': [{
                    'location': 0,
                    'length': len(user.first_name) + len(user.last_name) + 1
                }]
        }
    elif notification.type == 'fav':
        return {
            'text': "{0} {1} favorited your quote: \"{2}\"".format(user.first_name, user.last_name, quote.content),
            'bold': [{
                    'location': 0,
                    'length': len(user.first_name) + len(user.last_name) + 1
                }]
        }
    else:
        return None

def notification_dict_from_obj(notification):
    notification_res = dict()
    notification_res['_id'] = str(get_echo_id_from_quote_id(notification.quote_id))
    notification_res['type'] = notification.type
    notification_res['unread'] = notification.unread
    notification_res['timestamp'] = datetime_to_timestamp(notification.created) # doesn't jsonify
    notification_res['formatted-text'] = notification_to_text(notification)
    return notification_res

@app.route("/get_notifications", methods = ['get'])
def get_notifications():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        auth = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    #-----------------------------------

    fbid = request.args.get('fbid')
    unread_only = request.args.get('unread_only')
    limit = request.args.get('limit')

    try:
        user = User.query.filter_by(fbid = fbid).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        if not limit:
            if not unread_only:
                notifications = Notification.query.filter(Notification.recipients.any(User.id == user.id)).order_by(desc(Notification.id)).all()
            else:
                notifications = Notification.query.filter(Notification.recipients.any(User.id == user.id), Notification.unread).order_by(desc(Notification.id)).all()
        else:
            if not unread_only:
                notifications = Notification.query.filter(Notification.recipients.any(User.id == user.id)).order_by(desc(Notification.id)).limit(limit).all()
            else:
                notifications = Notification.query.filter(Notification.recipients.any(User.id == user.id), Notification.unread).order_by(desc(Notification.id)).limit(limit).all()

        result = []
        for notification in notifications:
            notification_res = notification_dict_from_obj(notification)
            result.append(notification_res)
            notification.unread = False

        db.session.commit() # update unreads

        dump = json.dumps(result)
        return format_response(result)
    except ServerException as e:
        return format_response(None, e)


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

#----------------------------------------
# Echo Auth
#----------------------------------------

# Note: does not comply with OAuth2 specifications - for internal use only

class AuthException(Exception):
    TOKEN_EXPIRED       = 1
    TOKEN_INVALID       = 2
    NOT_AUTHORIZED      = 3
    UNKNOWN_EXCEPTION   = 4 # so far: user 

    def __init__(self, message, n=UNKNOWN_EXCEPTION):
        self.message = message
        self.n = n

    # DON'T CHANGE THE AUTHEXCEPTION STRINGS
    def to_dict(self):
        return {'exception': 'AuthException', 'errno' : self.n, 'message' : self.message}

    def __str__(self):
        return "[%d] %s" % self.message

@app.route('/get_token', methods = ['GET'])
def get_token():
    # three cases: success, oauth error, network failure

    rand = random.randint(1, 100000)
    fbid = request.values.get('fbid')
    token = request.values.get('token')

    r = validate('fb', fbid, token)

    if not r:
        e = AuthException("Unable to validate user.", 4)
        return format_response(None, e)

    user_id = request.values.get('user_id')

    user = User.query.filter_by(fbid=fbid).first()
    if not user:
        db.session.add(User(fbid))
        db.session.commit()

    user = User.query.filter_by(fbid=fbid).first()

    # if user exists, update user in Access_Token table
    user_id = user.id
    access_token = manager.make_token({"user_id":user_id, "rand":rand})

    temp = Access_Token.query.filter_by(user_id=user_id).first()
    if temp:
        temp.access_token = access_token
    else:
        db.session.add(Access_Token(user_id, access_token))

    db.session.commit()

    response = {}
    response['user_id'] = user_id
    response['access_token'] = access_token
    dump = json.dumps(response)
    return format_response(response)

# determines whether the caller has access to the resources
def authorize_user(access_token):

    try:
        parsed_token = manager.parse_token(str(access_token))
        user_id = parsed_token['user_id']
    except ValueError as e:

        # note: these checks are dependent on exceptions in tokenlib library
        if "expired" in e.message:
            raise AuthException("Token is expired.", AuthException.TOKEN_EXPIRED)
        if "invalid" in e.message:
            raise AuthException("Token is invalid.", AuthException.TOKEN_INVALID)

        # safety
        raise AuthException("Something is wrong with the token.", AuthException.UNKNOWN_EXCEPTION)
    
    tok = Access_Token.query.filter_by(user_id=parsed_token['user_id']).first()
    if tok != None and int(tok.user_id) == int(user_id) and tok.access_token == access_token:
        return user_id

    raise AuthException("Not authorized.", AuthException.NOT_AUTHORIZED)

# check against fb to caller has access to the info
# returns True/False -- TODO: maybe make this raise an exception instead
def validate(method, user_id, token):

    is_valid = False

    if method == 'fb':

        # TODO: make robust against network failures
        data = {'fields':'id', 'access_token':token}
        url_data = urllib.urlencode(data)
        url = 'https://graph.facebook.com/me?{0}'.format(url_data)

        try:
            response = urllib2.urlopen(url)
        except urllib2.HTTPError, e:
            # do something again
            return is_valid
        except urllib2.URLError, e:
            return is_valid
            # fail or try again?

        r = json.load(response)

        try:
            if user_id == r['id']:
                is_valid = True
        except:
            is_valid = False

    return is_valid

# to be used as a decorator -- must return a callable
def authenticate(func):
    @wraps(func)
    def decorated_function(user_id="", access_token="", *args, **kwargs):
        try:
            authorize_user(user_id, access_token)
        except AuthException as e:
            return format_response(None, e)
        return func(*args, **kwargs)
    return decorated_function


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
