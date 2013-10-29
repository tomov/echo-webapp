# -*- coding: utf-8 -*-

from api_imports import *
from model import Favorite
from notif_api import add_notification

fav_api = Blueprint('fav_api', __name__)

@fav_api.route("/delete_fav/<quoteId>", methods = ['DELETE'])
@authenticate
@track
def delete_fav(quoteId, user_id = None):
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


@fav_api.route("/get_favs", methods = ['get'])
@authenticate
@track
def get_favs(user_id):
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


@fav_api.route("/add_fav", methods = ['POST'])
@authenticate
@track
def add_fav(user_id):
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
    
