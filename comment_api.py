# -*- coding: utf-8 -*-

import json
from flask import request

from application import app
from model import db, Comment


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


