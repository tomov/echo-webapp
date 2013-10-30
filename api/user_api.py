# -*- coding: utf-8 -*-

from api_imports import *
import random
import urllib
import urllib2

user_api = Blueprint('user_api', __name__)

## AUTH crap

@user_api.route('/get_token', methods = ['GET'])
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


## .. end AUTH crap


# also functions as update_user
@user_api.route("/add_user", methods = ['POST'])
@authenticate
@track
def add_user(user_id):
    udata = json.loads(request.values.get('data'))
    fbid = udata['id']
    picture_url = udata['picture_url']
    email = udata['email']
    first_name, last_name = split_name(udata['name'])
    friends_raw = udata['friends']
    unfriends_raw = udata.get('unfriends')
    clear_friends = udata.get('refreshing_entire_friend_list')

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
            if clear_friends:
                user.friends[:] = []
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


# by the way, this naming convention is simply atrocious...
# this is for registering DEVICE tokens, not USER ACCESS tokens (which in turn are completely different from their Facebook access tokens btw...)
@user_api.route("/register_token", methods = ['POST'])
@authenticate
@track
def register_device_token(user_id):
    qdata = json.loads(request.values.get('data'))
    userDeviceToken = qdata['token']

    try:
        user = User.query.filter(User.id == user_id).first()
        if not user:
            raise ServerException(ErrorMessage.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        user_with_same_token = User.query.filter_by(device_token=userDeviceToken).first()
        if user_with_same_token and user_with_same_token.id != user.id:
            raise ServerException(ErrorMessages.DEVICE_TOKEN_EXISTS, \
                ServerException.ER_BAD_TOKEN)

        if userDeviceToken:
            user.device_token = userDeviceToken
        else:
            user.device_token = None

        db.session.commit()
        return format_response(SuccessMessages.TOKEN_REGISTERED)

    except ServerException as e:
        return format_response(None, e)
