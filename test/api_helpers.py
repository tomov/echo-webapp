import sys

sys.path.append('..') # hack to be able to import files from parent directory without messing with modules
from model import db
from model import User, Quote
from mock_data import MockUserData
import json

class UserAPIHelpers():

    def get_token_for_user_with_fbid(self, user_fbid):
        rv = self.app.get('/get_token?fbid=%s&token=%s' % (user_fbid, MockUserData.fbids_tokens.get(user_fbid)))
        rv = json.loads(rv.data)
        return rv.get('access_token');

    def add_user(self, user_dict):
        token = self.get_token_for_user_with_fbid(user_dict['id'])
        self.app.post('/add_user?token=%s' % token, data=dict(data=json.dumps(user_dict)))

    def register_device_token(self, token_dict, user_fbid):
        # TODO(mom) this nomenclature makes my eyes bleed... why do we call both user tokens and device tokens with the same name?
        # we should resolve it somehow, because this is ridiculous... just look at the POST url below
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.post('/register_token?token=%s' % token, data=dict(data=json.dumps(token_dict)))


class QuoteAPIHelpers(UserAPIHelpers):

    def add_quote(self, quote_dict, user_fbid = None):
        if user_fbid is None:
            user_fbid = quote_dict['reporterFbid']
        token = self.get_token_for_user_with_fbid(user_fbid)
        rv = self.app.post('/add_quote?token=%s' % token, data=dict(data=json.dumps(quote_dict)))
        rv = json.loads(rv.data)
        return rv

    def add_quote_to_db(self, quote_dict, deleted = False):
        source = User.query.filter_by(fbid=quote_dict['sourceFbid']).first()
        reporter = User.query.filter_by(fbid = quote_dict['reporterFbid']).first()
        if not source:
            return False
        if not reporter:
            return False
        quote = Quote(source.id, 
            reporter.id, 
            quote_dict['quote'], 
            quote_dict.get('location'), 
            quote_dict.get('location_lat'), 
            quote_dict.get('location_long'), 
            deleted)
        quote.echoers.append(reporter)
        db.session.add(quote)
        db.session.commit()
        return True

    def delete_quote(self, quote_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.delete('/delete_quote/%s?token=%s' % (quote_id, token))

    def get_quote(self, echo_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        rv = self.app.get('/get_quote?order_id=%s&token=%s' % (echo_id, token))
        rv = json.loads(rv.data)
        return rv

    def check_deleted_quotes(self, echo_ids, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        rv = self.app.post('/check_deleted_quotes?token=%s' % token, data=dict(data=json.dumps(echo_ids)))
        rv = json.loads(rv.data)
        return rv

    def get_quotes(self, user_fbid, limit, latest = None, oldest = None, profile_fbid = None):
        token = self.get_token_for_user_with_fbid(user_fbid)
        url = '/get_quotes?token=%s&limit=%s' % (token, limit)
        if latest is not None:
            url = (url + '&latest=%s') % latest
        if oldest is not None:
            url = (url + '&oldest=%s') % oldest
        if profile_fbid is not None:
            url = (url + '&profile_fbid=%s') % profile_fbid
        rv = self.app.get(url)
        rv = json.loads(rv.data)
        return rv


class CommentAPIHelpers(QuoteAPIHelpers):

    def add_comment(self, comment_dict, user_fbid = None):
        if user_fbid is None:
            user_fbid = comment_dict['userFbid']
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.post('/add_comment?token=%s' % token, data=dict(data=json.dumps(comment_dict)))

    def delete_comment(self, comment_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.delete('/delete_comment/%s?token=%s' % (comment_id, token))


class FavAPIHelpers(QuoteAPIHelpers):

    def add_fav(self, quote_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.post('/add_fav?token=%s' % token, data=dict(data=json.dumps({'quoteId': quote_id})))

    def delete_fav(self, quote_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.delete('/delete_fav/%s?token=%s' % (quote_id, token))

    def get_favs(self, quote_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        rv = self.app.get('/get_favs?quoteId=%s&token=%s' % (quote_id, token))
        rv = json.loads(rv.data)
        return rv


class EchoAPIHelpers(QuoteAPIHelpers):

    def add_echo(self, quote_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.post('/add_echo?token=%s' % token, data=dict(data=json.dumps({'quoteId': quote_id})))

    def delete_echo(self, quote_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.delete('/delete_echo/%s?token=%s' % (quote_id, token))

    def get_echoers(self, quote_id, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        rv = self.app.get('/get_echoers?quoteId=%s&token=%s' % (quote_id, token))
        rv = json.loads(rv.data)
        return rv


class NotifAPIHelpers(QuoteAPIHelpers, CommentAPIHelpers, FavAPIHelpers, EchoAPIHelpers):

    def get_notifications(self, unread_only, limit, clear, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        if limit is None:
            rv = self.app.get('/get_notifications?unread_only=%s&clear=%s&token=%s' % (unread_only, clear, token))
        else:
            rv = self.app.get('/get_notifications?unread_only=%s&limit=%s&clear=%s&token=%s' % (unread_only, limit, clear, token))
        rv = json.loads(rv.data)
        return rv

    def get_notifprefs(self, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        rv = self.app.get('/get_notifprefs?token=%s' % token)
        rv = json.loads(rv.data)
        return rv

    def set_notifprefs(self, prefs_dict, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.post('/set_notifprefs?token=%s' % token, data=dict(data=json.dumps(prefs_dict)))


class MiscAPIHelpers(UserAPIHelpers):

    def add_feedback(self, feedback_dict, user_fbid):
        token = self.get_token_for_user_with_fbid(user_fbid)
        self.app.post('/add_feedback?token=%s' % token, data=dict(data=json.dumps(feedback_dict)))
