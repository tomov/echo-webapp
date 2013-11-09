# -*- coding: utf-8 -*-

from api_imports import *
from sqlalchemy import or_, and_, desc
from sets import Set

from model import Echo, Favorite, Comment
from notif_api import add_notification

quote_api = Blueprint('quote_api', __name__)

@quote_api.route("/add_quote", methods = ['POST'])
@authenticate
@track
def add_quote(user_id):
    qdata = json.loads(request.values.get('data'))
    sourceFbid = qdata['sourceFbid']
    reporterFbid = qdata['reporterFbid']
    content = qdata['quote']
    location = qdata.get('location')
    location_lat = qdata.get('location_lat')
    location_long = qdata.get('location_long')

    try:
        source = User.query.filter_by(fbid = sourceFbid).first()
        reporter = User.query.filter_by(fbid = reporterFbid).first()
        if not source:
            raise ServerException(ErrorMessages.SOURCE_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        if not reporter:
            raise ServerException(ErrorMessages.REPORTER_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        if source.id == reporter.id:
            raise ServerException(ErrorMessages.SAME_SOURCE_REPORTER, \
                ServerException.ER_BAD_QUOTE)

        quote = Quote(source.id, reporter.id, content, location, location_lat, location_long, False)
        # add the reporter as the first "echoer"
        # this creates a dummy entry in the echoes table that corresponds to the original quote, with echo.user_id == quote.reporter_id
        # this makes it easier to fetch quotes and echoes chronologically in get_quotes
        quote.echoers.append(reporter)
        db.session.add(quote)
        db.session.flush() # so we can get quote id

        add_notification(reporter, quote, 'quote', source.id)
        db.session.commit()

        echo = Echo.query.filter_by(quote_id=quote.id).first()
        return json.dumps({'echo_id': echo.id})
    except ServerException as e:
        return format_response(None, e)


def quote_dict_from_obj(quote):
    quote_res = dict()
    quote_res['_id'] = str(quote.id)
    quote_res['source_name'] = quote.source.first_name + ' ' + quote.source.last_name
    quote_res['source_picture_url'] = quote.source.picture_url
    quote_res['reporter_name'] = quote.reporter.first_name + ' ' + quote.reporter.last_name
    quote_res['reporter_picture_url'] = quote.reporter.picture_url
    quote_res['timestamp'] = datetime_to_timestamp(quote.created) # doesn't jsonify
    quote_res['sourceFbid'] = quote.source.fbid
    quote_res['reporterFbid'] = quote.reporter.fbid
    quote_res['location'] = quote.location
    quote_res['location_lat'] = quote.location_lat
    quote_res['location_long'] = quote.location_long
    quote_res['quote'] = quote.content
    quote_res['echo_count'] = len(quote.echoers) - 1   # subtract the dummy echo where echo.user_id == quote.reporter_id
    quote_res['fav_count'] = len(quote.favs)
    return quote_res

@quote_api.route("/get_quote", methods = ['get'])
@authenticate
@track
def get_quote(user_id):
    echoId = request.args.get('order_id')

    try:
        echo = Echo.query.filter_by(id = echoId).first()
        if not echo:
            raise ServerException(ErrorMessages.ECHO_NOT_FOUND, \
                ServerException.ER_BAD_ECHO)
        quote = echo.quote
        if not quote or quote.deleted:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        user = User.query.filter_by(id = user_id).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        ids = [friend.id for friend in user.all_friends] + [user.id]

        # TODO there is some code duplication with get_quotes below... we should think if it could be avoided
        is_echo = echo.user_id != quote.reporter_id
        if is_echo:
            quote.created = echo.created
            quote.reporter = echo.user
        quote_res = quote_dict_from_obj(quote)
        # TODO is there a better way to do this? e.g. user in quote.fav_users
        # tho it might be a heavier operation behind the scenes
        quote_res['user_did_fav'] = Favorite.query.filter_by(quote_id=quote.id, user_id=user.id).count() > 0
        quote_res['user_did_echo'] = user.id != quote.reporter_id and Echo.query.filter_by(quote_id=quote.id, user_id=user.id).count() > 0
        quote_res['is_echo'] = is_echo
        quote_res['order_id'] = echo.id

        quote_res['comments'] = []
        comments = Comment.query.filter_by(quote_id = quote.id).order_by(Comment.created) # TODO figure out how to do it nicer using quote.comments with an implicit order_by defined as part of the relationship in model.py. Note that without the order_by it stil works b/c it returns them in order of creation, so technically we could still use quote.comments, however that would induce too much coupling between how sqlalchemy works and our code. Check out http://stackoverflow.com/questions/6750251/sqlalchemy-order-by-on-relationship-for-join-table 
        for comment in comments:
            comment_res = dict()
            comment_res['id'] = comment.id
            comment_res['fbid'] = comment.user.fbid
            comment_res['timestamp'] = datetime_to_timestamp(comment.created)
            comment_res['comment'] = comment.content
            comment_res['name'] = comment.user.first_name + ' ' + comment.user.last_name
            comment_res['picture_url'] = comment.user.picture_url
            comment_res['is_friend_or_me'] = comment.user_id in ids
            quote_res['comments'].append(comment_res)

        return format_response(quote_res);
    except ServerException as e:
        return format_response(None, e);

# TODO maybe deprecate get_quotes_with_ids? this is basically the same thing
@quote_api.route('/check_deleted_quotes', methods = ['post'])
@authenticate
@track
def check_deleted_quotes(user_id):
    order_ids = json.loads(request.values.get('data'))

    result = []
    for order_id in order_ids:
        echo = Echo.query.filter_by(id = order_id).first()
        if not echo or not echo.quote or echo.quote.deleted:
            result.append(None)
        else:
            result.append({'order_id': order_id})

    return format_response(result)

@quote_api.route('/get_quotes_with_ids', methods = ['post'])
@authenticate
@track
def get_quotes_with_ids(user_id):
    ids = json.loads(request.values.get('data'))

    result = []
    for id in ids:
        quote = Quote.query.filter_by(id = id).first()
        if not quote or quote.deleted:
            result.append(None)
        else:
            result.append(quote_dict_from_obj(quote))

    return format_response(result)


@quote_api.route("/get_quotes", methods = ['get'])
@authenticate
@track
def get_quotes(user_id):
    #fbid = request.args.get('fbid') # TODO: remove this
    oldest = request.args.get('oldest')
    latest = request.args.get('latest')
    limit = request.args.get('limit')
    profile_fbid = request.args.get('profile_fbid')

    try:
        # fetch observing user, i.e. user who requeste the feed
        user = User.query.filter(User.id == user_id).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)
        # if no profile_fbid is given, the user is looking at her feed
        if not profile_fbid:
            profile_fbid = user.fbid
            req_type = 'feed'
        # otherwise, she is looking at a profile page (potentially her own)
        else:
            req_type = 'profile'

        if not limit:
            raise ServerException("Rishi you're not passing me a limit", \
                ServerException.ER_BAD_PARAMS)

        # fetch user whose feed/profile we're looking at
        profile_user = User.query.filter(User.fbid == profile_fbid).first()
        if not profile_user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        ## construct OR condition for which quotes to pick
        if req_type == 'profile':
            ids = []
        else:
            ids = [friend.id for friend in profile_user.all_friends]
        ids.append(profile_user.id)
        or_conds = or_(Echo.quote.has(Quote.source_id.in_(ids)), Echo.quote.has(Quote.reporter_id.in_(ids)), Echo.user_id.in_(ids))

        ## fetch all quotes in user feed, only id's first
        ## note that we're using the echo table as a reference to quotes, even for original ones. We're not querying the quotes table
        ## this is so we have to deal with only one id's sequence (the one for echoes) rather than two
        ## then we manually iterate and filter by limit, upper/lower limits, etc
        ## this is the most efficient way momchil came up to do it for now

        # THIS IS A TEMPORARY HACK FOR HACKPRINCETON to make this one big feed
        if req_type == 'profile':
            echoes = Echo.query.with_entities(Echo.id, Echo.quote_id).filter(or_conds, Echo.quote.has(Quote.deleted == False)).order_by(Echo.id)
        else:
            echoes = Echo.query.with_entities(Echo.id, Echo.quote_id).filter(Echo.quote.has(Quote.deleted == False)).order_by(Echo.id)

        # get bounds
        if latest and oldest:
            upper = int(latest)
            lower = int(oldest) 
            if lower > upper:
                lower, upper = upper, lower
        elif latest:
            lower = int(latest) 
        elif oldest:
            upper = int(oldest)

        # iterate over quotes in feed and get oldest instances, also filter by oldest/latest/limit/etc
        # also remove duplicates -- only leave the oldest version of each quote that the user has seen.
        # note that for that purpose, we have the results in increasing order of id's, and we have to reverse it at the end
        # TODO FIXME this is terrible... this should be entirely MySQL side.... learn some sqlalchemy / sql and do it
        seen_quote_ids = Set()
        echo_ids = []
        for echo in echoes:
            quote_id = echo.quote_id
            # only consider first instance of quote that the user sees
            if quote_id in seen_quote_ids:
                continue
            seen_quote_ids.add(quote_id)
            # see if echo falls in requested bounds, if any
            if latest and oldest:
                if not (echo.id >= lower and echo.id <= upper):
                    continue
            elif latest:
                if not (echo.id > lower):
                    continue
            elif oldest:
                if not (echo.id < upper):
                    continue
            echo_ids.append(echo.id)
        echo_ids.reverse()
        # at this point echo_ids is in descending order of id, i.e. the order in which we will return
        limit = int(limit)
        echo_ids = echo_ids[0:limit]

        # make another request, this time for the specific echo id's... TODO FIXME super lame...
        echoes = Echo.query.filter(Echo.id.in_(echo_ids)).order_by(desc(Echo.id))
        result = []
        for echo in echoes:
            quote = echo.quote
            # the echo corresponds to the original quote iff echo.user_id == quote.reporter_id
            is_echo = echo.user_id != quote.reporter_id
            if is_echo:
                quote.created = echo.created
                quote.reporter = echo.user
            quote_res = quote_dict_from_obj(quote)
            # TODO is there a better way to do this? e.g. user in quote.fav_users
            # tho it might be a heavier operation behind the scenes
            quote_res['user_did_fav'] = Favorite.query.filter_by(quote_id=quote.id, user_id=user.id).count() > 0
            quote_res['user_did_echo'] = user.id != quote.reporter_id and Echo.query.filter_by(quote_id=quote.id, user_id=user.id).count() > 0
            quote_res['is_echo'] = is_echo
            quote_res['order_id'] = echo.id
            result.append(quote_res)

        #sorted_result = sorted(result, key = lambda k: k['timestamp'], reverse=True) -- we don't need this anymore, leaving it here for syntax reference on how to sort array of dictionaries
        dump = json.dumps(result)
        return format_response(result)
    except ServerException as e:
        return format_response(None, e)



@quote_api.route("/delete_quote/<quoteId>", methods = ['DELETE'])
@authenticate
@track
def delete_quote(quoteId, user_id = None):
    try:
        user = User.query.filter_by(id = user_id).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        quote = Quote.query.filter_by(id = quoteId).first()
        if not quote or quote.deleted:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        if user.id == quote.reporter.id or user.id == quote.source.id:
            quote.deleted = True
            db.session.commit()
        return format_response(SuccessMessages.QUOTE_DELETED)
    except ServerException as e:
        return format_response(None, e)

