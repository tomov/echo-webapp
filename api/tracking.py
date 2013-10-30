# -*- coding: utf-8 -*-

from flask import request
from functools import wraps
from model import db, APIEvent

# log api call
def track_event(user_id, name, request_size, response_size):
    # TODO record average request and response size
    # must update db schema and reflect both locally and remotely
    print 'track: {0} calls {1}: input = {2}, output = {3}'.format(user_id, name, request_size, response_size)
    event = APIEvent(user_id, name, request_size, response_size)
    db.session.add(event)
    db.session.commit()


# used as a decorator to log api function calls
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

