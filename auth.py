# -*- coding: utf-8 -*-

from flask import request
from functools import wraps
import tokenlib

from model import db, Access_Token, APIEvent
from util import *

# used for auth - 1 year = 31560000, 1 month = ?, 
manager = tokenlib.TokenManager(secret="sL/mZPxS:]CI)@OWpP!GR9![a.&{i)i", timeout=7776000)

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


def track_event(user_id, name, request_size, response_size):
    # TODO record average request and response size
    # must update db schema and reflect both locally and remotely
    print 'track: {0} calls {1}: input = {2}, output = {3}'.format(user_id, name, request_size, response_size)
    event = APIEvent.query.filter_by(user_id=user_id, name=name).first()
    if event:
        event.count = event.count + 1
    else:
        event = APIEvent(user_id, name)
        db.session.add(event)
    db.session.commit()


def track(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        user_id = kwargs['user_id']
        response = func(*args, **kwargs)
        data_len = 0
        if request.values.get('data') is not None:
            data_len = len(request.values.get('data'))
        track_event(user_id, func.__name__, data_len, len(response))
        return response
    return decorated_function

# used as a decorator around api function calls
# note that decorated api method must expect a user_id parameter
def authenticate(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        token = request.args.get('token')
        try:
            user_id = authorize_user(token)
        except AuthException as e:
            return format_response(None, e)
        kwargs['user_id'] = user_id
        return func(*args, **kwargs)
    return decorated_function


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
