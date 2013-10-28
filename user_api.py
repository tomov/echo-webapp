# -*- coding: utf-8 -*-

import json
from flask import request

from application import app
from model import db, User

## AUTH crap

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

    if token == "universal_access_token_TODO_this_must_be_gone_ASAP--see_facebook_test_users":
        return True

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



## .. end AUTH crap


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
            # user does not exist in db -- this is impossible since she must have gotten an access token
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        else:
            # user was pre-signed up by a friend but that's the first time she's logging in
            # or user is logging in for first time
            user.registered = True
            user.email = email
            user.picture_url = picture_url
            user.first_name = first_name.decode('utf8')
            user.last_name = last_name.decode('utf8')
#            if unfriends_raw is None:
#                user.friends.clear()
            add_friends(user, friends_raw)
            remove_friends(user, unfriends_raw)

        db.session.commit()
        return format_response(SuccessMessages.USER_ADDED)
    except ServerException as e:
        return format_response(None, e)


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
        if user in friend.friends:
            friend.friends.remove(user)





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

