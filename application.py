import os
from flask import Flask, request
import json
from sqlalchemy import or_, and_
import time
from sqlalchemy import desc
from pprint import pprint
from sets import Set
import datetime

import model
from model import db
from model import User, Quote, Comment, Favorite, Echo, Feedback, Access_Token, Notification, NotifPrefs, APIEvent
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
    #user = User.query.filter(User.id==6713).first()
    #quote = Quote.query.filter(Quote.source_id==6713).first()
    #add_notification(user, quote, 'quote', 6189)
    create_db()
    #user = User.query.filter_by(id=6587).first()
    #db.session.delete(user)
    #db.session.commit()
    return "Hello from Python yay!"

@app.route("/test_notif")
def test_notif():
    # Send a notification
    #token_hex1 = '04c11da985c7e9a615ddc039ce654b76e096db088602e71f8bbfc9fb6d59a91e' # rishi's phone
    #token_hex1 = '884a19da5dc0a72d8aecb5ad6fe7ee2e49e9d8aacd618aedb785f067cb114de1' # rishi's phone 2
    #token_hex1 = 'a40a3af5b674bc891614ecaf7a4d528150264e90a2dc1b16756148e14d41be64' # jacob's
    #token_hex1 = '5093a4269fb4065bd70b6e23aed3f40b8978e1335cd0b889c9ed99c6c2d30631' # chris
    #token_hex1 = 'a6f283a5eff9cd231efb1980558795a0443833d5d6470b61e972c8f786b9ae3f' # juan
    token_hex1 = 'a951d8aba5ec3532edc6426583681e3749e2b71c9e1724219897382efd8154b0' # momchil
    #payload = Payload(alert="Someone quoted you!", sound="default", badge=1)
    send_notification(token_hex1, "this is a test notification")
    return "YES"

#---------------------------------------
#         Helper functions
#----------------------------------------

def send_notification(token_hex, text):
    apns = APNs(use_sandbox=False, cert_file='certificates/EchoAPNSProdCert.pem', key_file='certificates/newEchoAPNSProdKey.pem')
    payload = Payload(alert=text, sound="default", badge=0)
    apns.gateway_server.send_notification(token_hex, payload)

def track_event(user_id, name):
    event = APIEvent.query.filter_by(user_id=user_id, name=name).first()
    if event:
        event.count = event.count + 1
    else:
        event = APIEvent(user_id, name)
        db.session.add(event)
    db.session.commit()

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
    track_event(auth, "add_user")
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
        user_id = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    track_event(user_id, "update_user")
    #-----------------------------------

    udata = json.loads(request.values.get('data'))
    picture_url = None
    email = None
    first_name = None
    last_name = None
    friends_raw = None
    if 'picture_url' in udata:
        picture_url = udata['picture_url']
    if 'email' in udata:
        email = udata['email']
    if 'name' in udata:
        first_name, last_name = split_name(udata['name'])
    if 'friends' in udata:
        friends_raw = udata['friends']

    try:
        user = User.query.filter_by(id = user_id).first()
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

    #print 'ADD NOTIFICATION from user ' + str(user.id) + ' quote ' + str(quote.id) + ' type ' + str(type) + ' for recipient ' + str(recipient_id)
    # add notification to db
    recipient = User.query.filter_by(id=recipient_id).first()
    if not recipient:
        return
    if recipient not in user.friends:
        return
    if not recipient.registered:
        return
    ids = [friend.id for friend in recipient.friends] + [recipient.id]
    echo = Echo.query.filter(Echo.quote == quote, Echo.user_id.in_(ids)).order_by(Echo.id).first()

    notification = Notification(user, quote, echo, type)
    notification.recipients.append(recipient)
    db.session.add(notification)

    # send push notification to device
    formatted_text = notification_to_text(notification)
    token_hex = recipient.device_token
    if not token_hex:
        return
    #print 'send text ' + formatted_text['text']
    try:
        send_notification(token_hex, formatted_text['text'])
    except Exception as e:
        #raise  # TODO FIXME this is for debugging purposes only -- remove after testing!
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
    track_event(auth, "add_quote")
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
        user_id = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    track_event(user_id, "add_comment")
    #-----------------------------------

    qdata = json.loads(request.values.get('data'))
    quoteId = qdata['quoteId']
    content = qdata['comment']

    try:
        user = User.query.filter_by(id = user_id).first()
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
        user_id = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    track_event(user_id, "add_echo")
    #-----------------------------------

    qdata = json.loads(request.values.get('data'))
    quoteId = qdata['quoteId']

    try:
        user = User.query.filter_by(id = user_id).first()
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
        user_id = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    track_event(user_id, "add_fav")
    #-----------------------------------

    qdata = json.loads(request.values.get('data'))
    quoteId = qdata['quoteId']

    try:
        user = User.query.filter_by(id = user_id).first()
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
            return format_response(ErrorMessages.FAV_ALREADY_EXISTS);

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
    user_id = 0
    try:
        user_id = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    track_event(user_id, "register_token")
    #-----------------------------------

    qdata = json.loads(request.values.get('data'))
    userDeviceToken = qdata['token']

    print userDeviceToken

    try:
        user = User.query.filter(User.id == user_id).first()
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
        user_id = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    track_event(user_id, "add_feedback")
    #-----------------------------------

    data = json.loads(request.values.get('data'))
    content = data['content']
    version = data['version']
   
    try:
        user = User.query.filter_by(id = user_id).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        feedback = Feedback(user_id, content, version)
        db.session.add(feedback)
        db.session.commit()
        return format_response(SuccessMessages.FEEDBACK_ADDED)
    except ServerException as e:
        return format_response(None, e)

# TODO this is just for Apple
@app.route('/add_feedback_from_support', methods = ['POST'])
def add_feedback_from_support():
    name = request.form['name']
    email = request.form['email']
    text = request.form['text']

    content = json.dumps({'name': name, 'email': email, 'text': text});
    feedback = Feedback(6416, content)
    db.session.add(feedback)
    db.session.commit()
    return '<p style="align: center">Thank you for your feedback! We will review it and get back to you as soon as possible.</p>'

@app.route("/set_notifprefs", methods = ['post'])
def set_notifprefs():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        user_id = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    track_event(user_id, "set_notifprefs")
    #-----------------------------------

    data = json.loads(request.values.get('data'))
    quotes = data.get('quotes')
    echoes = data.get('echoes')
    comments = data.get('comments')
    favs = data.get('favs')

    try:
        user = User.query.filter(User.id == user_id).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        if quotes is not None:
            user.notifprefs.quotes = quotes
        if echoes is not None:
            user.notifprefs.echoes = echoes
        if comments is not None:
            user.notifprefs.comments = comments
        if favs is not None:
            user.notifprefs.favs = favs
        db.session.commit()

        return format_response(SuccessMessages.NOTIFPREFS_SET)
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
        user_id = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    track_event(user_id, "delete_quote")
    #-----------------------------------

    try:
        user = User.query.filter_by(id = user_id).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote or quote.deleted:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        if user == quote.reporter or user == quote.source:
            quote.deleted = True
            db.session.commit()
        return format_response(SuccessMessages.QUOTE_DELETED)
    except ServerException as e:
        return format_response(None, e)


@app.route("/delete_echo/<quoteId>", methods = ['DELETE'])
def delete_echo(quoteId):

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        user_id = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    track_event(user_id, "delete_echo")
    #-----------------------------------

    try:
        user = User.query.filter_by(id = user_id).first()
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
    track_event(auth, "delete_friendship")
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
    track_event(auth, "delete_comment")
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


@app.route("/delete_fav/<quoteId>", methods = ['DELETE'])
def remove_fav(quoteId):

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        user_id = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    track_event(user_id, "remove_fav")
    #-----------------------------------

    try:
        user = User.query.filter_by(id = user_id).first()
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
        user_id = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    track_event(user_id, "get_quote")
    #-----------------------------------

    echoId = request.args.get('order_id')

    try:
        echo = Echo.query.filter_by(id = echoId).first()
        if not echo:
            raise ServerException(ErrorMessages.ECHO_NOT_FOUND, \
                ServerException.ER_BAD_ECHO)
        quote = echo.quote
        if not quote or quote.deleted:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        user = User.query.filter_by(id = user_id).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        ids = [friend.id for friend in user.friends] + [user.id]

        # TODO there is some code duplication with get_quotes below... we should think if it could be avoided
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
        quote_res['order_id'] = echo.id

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
    track_event(auth, "check_deleted_quotes")
    #-----------------------------------

    order_ids = json.loads(request.values.get('data'))

    result = []
    for order_id in order_ids:
        echo = Echo.query.filter_by(id = order_id).first()
        if not echo or not echo.quote or echo.quote.deleted:
            result.append(None)
        else:
            result.append({'order_id': order_id})

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
    track_event(auth, "get_quotes_with_ids")
    #-----------------------------------

    ids = json.loads(request.values.get('data'))

    result = []
    for id in ids:
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
    user_id = 0
    try:
        user_id = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    track_event(user_id, "get_quotes")
    #-----------------------------------

    #fbid = request.args.get('fbid') # TODO: remove this
    oldest = request.args.get('oldest')
    latest = request.args.get('latest')
    limit = request.args.get('limit')
    profile_fbid = request.args.get('profile_fbid')

    try:
        # fetch observing user, i.e. user who requeste the feed
        user = User.query.filter(User.id == user_id).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        # if no profile_fbid is given, the user is looking at her feed
        if not profile_fbid:
            profile_fbid = user.fbid
            req_type = 'feed'
        # otherwise, she is looking at a profile page (potentially her own)
        else:
            req_type = 'profile'

        if not limit:
            raise ServerException("Rishi you're not passing me a limit", \
                ServerException.ER_BAD_PARAMS)

        # fetch user whose feed/profile we're looking at
        profile_user = User.query.filter(User.fbid == profile_fbid).first()
        if not profile_user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        ## construct OR condition for which quotes to pick
        if req_type == 'profile':
            ids = []
        else:
            ids = [friend.id for friend in profile_user.friends]
        ids.append(profile_user.id)
        or_conds = or_(Echo.quote.has(Quote.source_id.in_(ids)), Echo.quote.has(Quote.reporter_id.in_(ids)), Echo.user_id.in_(ids))

        ## fetch all quotes in user feed, only id's first
        ## note that we're using the echo table as a reference to quotes, even for original ones. We're not querying the quotes table
        ## this is so we have to deal with only one id's sequence (the one for echoes) rather than two
        ## then we manually iterate and filter by limit, upper/lower limits, etc
        ## this is the most efficient way momchil came up to do it for now
        echoes = Echo.query.with_entities(Echo.id, Echo.quote_id).filter(or_conds, Echo.quote.has(Quote.deleted == False)).order_by(Echo.id)

        # get bounds
        if latest and oldest:
            upper = int(latest)
            lower = int(oldest) 
            if lower > upper:
                lower, upper = upper, lower
        elif latest:
            lower = int(latest) 
        elif oldest:
            upper = int(oldest)

        # iterate over quotes in feed and get oldest instances, also filter by oldest/latest/limit/etc
        # also remove duplicates -- only leave the oldest version of each quote that the user has seen.
        # note that for that purpose, we have the results in increasing order of id's, and we have to reverse it at the end
        # TODO FIXME this is terrible... this should be entirely MySQL side.... learn some sqlalchemy / sql and do it
        seen_quote_ids = Set()
        echo_ids = []
        for echo in echoes:
            quote_id = echo.quote_id
            # only consider first instance of quote that the user sees
            if quote_id in seen_quote_ids:
                continue
            seen_quote_ids.add(quote_id)
            # see if echo falls in requested bounds, if any
            if latest and oldest:
                if not (echo.id >= lower and echo.id <= upper):
                    continue
            elif latest:
                if not (echo.id > lower):
                    continue
            elif oldest:
                if not (echo.id < upper):
                    continue
            echo_ids.append(echo.id)
        echo_ids.reverse()
        # at this point echo_ids is in descending order of id, i.e. the order in which we will return
        limit = int(limit)
        echo_ids = echo_ids[0:limit]

        # make another request, this time for the specific echo id's... TODO FIXME super lame...
        echoes = Echo.query.filter(Echo.id.in_(echo_ids)).order_by(desc(Echo.id))
        result = []
        for echo in echoes:
            quote = echo.quote
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
            quote_res['order_id'] = echo.id
            result.append(quote_res)

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
    track_event(auth, "get_echoers")
    #-----------------------------------

    quoteId = request.args.get('quoteId')

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
    track_event(auth, "get_favs")
    #-----------------------------------

    quoteId = request.args.get('quoteId')

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
    content = quote.content
    if content[-1:].isalpha() or content[-1:].isdigit():
        content += '.'
    if notification.type == 'quote':
        return {
            'text': "{0} {1} posted a quote by you!".format(user.first_name, user.last_name),
            'bold': [{
                    'location': 0,
                    'length': len(user.first_name) + len(user.last_name) + 1
                }]
        }
    elif notification.type == 'echo':
        return {
            'text': "{0} {1} echoed your quote: \"{2}\"".format(user.first_name, user.last_name, content),
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
            'text': "{0} {1} favorited your quote: \"{2}\"".format(user.first_name, user.last_name, content),
            'bold': [{
                    'location': 0,
                    'length': len(user.first_name) + len(user.last_name) + 1
                }]
        }
    else:
        return None

def notification_dict_from_obj(notification):
    notification_res = dict()
    notification_res['_id'] = str(notification.quote_id)
    notification_res['order_id'] = str(notification.echo_id)
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
    user_id = 0
    try:
        user_id = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    track_event(user_id, "get_notifications")
    #-----------------------------------

    unread_only = request.args.get('unread_only')
    limit = request.args.get('limit')
    clear = request.args.get('clear')

    try:
        user = User.query.filter(User.id == user_id).first()
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
            if clear:
                notification.unread = False

        db.session.commit() # update unreads

        return format_response(result)
    except ServerException as e:
        return format_response(None, e)


@app.route("/get_notifprefs", methods = ['get'])
def get_notifprefs():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        user_id = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    track_event(user_id, "get_notifprefs")
    #-----------------------------------

    try:
        user = User.query.filter(User.id == user_id).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        if not user.notifprefs:
            user.notifprefs = NotifPrefs()
            db.session.commit()

        notifprefs = {
            'quotes': user.notifprefs.quotes,
            'echoes': user.notifprefs.echoes,
            'comments': user.notifprefs.comments,
            'favs': user.notifprefs.favs
        }

        return format_response(notifprefs)
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
        # TODO: make this uint or long (when we have billions of users...)
        return int(user_id)

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
