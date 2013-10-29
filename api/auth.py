# -*- coding: utf-8 -*-

from flask import request
from functools import wraps
import tokenlib

from model import db, Access_Token, APIEvent
from util import *
from common import *

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