# -*- coding: utf-8 -*-

import json
from flask import request

from application import app
from model import db, Favorite


@app.route("/delete_fav/<quoteId>", methods = ['DELETE'])
def delete_fav(quoteId):

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
    
