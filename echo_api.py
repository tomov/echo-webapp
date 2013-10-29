# -*- coding: utf-8 -*-

import json
from flask import request, Blueprint

from model import db, User, Quote, Echo
from auth import *
from util import *
from constants import *
from notif_api import add_notification

echo_api = Blueprint('echo_api', __name__)

@echo_api.route("/get_echoers", methods = ['get'])
@authenticate
@track
def get_echoers(user_id):
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


@echo_api.route("/add_echo", methods = ['POST'])
@authenticate
@track
def add_echo(user_id):
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


@echo_api.route("/delete_echo/<quoteId>", methods = ['DELETE'])
@authenticate
@track
def delete_echo(quoteId, user_id = None):
    try:
        user = User.query.filter_by(id = user_id).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote or quote.deleted:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        if user in quote.echoers and user.id != quote.reporter.id and user.id != quote.source.id:
            quote.echoers.remove(user)
            db.session.commit()
        return format_response(SuccessMessages.ECHO_DELETED)
    except ServerException as e:
        return format_response(None, e)