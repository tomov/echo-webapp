# -*- coding: utf-8 -*-

import json
from flask import request

from application import app
from model import db, Echo

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

        if user not in quote.echoers and user.id != quote.reporter.id and user.id != quote.source.id:
            quote.echoers.append(user)
            add_notification(user, quote, 'echo', quote.reporter_id)
            add_notification(user, quote, 'echo', quote.source_id)
        db.session.commit()
        return format_response(SuccessMessages.ECHO_ADDED)
    except ServerException as e:
        return format_response(None, e)

