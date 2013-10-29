import base
from base import *
import api_helpers
from api_helpers import *
import mock_data
from mock_data import *

from model import Notification

class TestNotifAPI(TestBase, NotifAPIHelpers, MockUserData, MockQuoteData, MockCommentData):

    def setUp(self):
        TestBase.setUp(self)
        self.add_user(self.user_simple) # reporter
        self.add_user(self.user_with_friends) # source

    # ------------- helpers -------------

    # check if db entry notif after add_notification is the same as notif_dict
    def assert_is_same_notif(self, notif, notif_dict):
        self.assertEqual(notif.user_id, notif_dict['user_id'])
        self.assertEqual(notif.type, notif_dict['type'])
        self.assertEqual(notif.quote_id, notif_dict['quote_id'])
        self.assertEqual(notif.echo_id, notif_dict['echo_id'])

    # ------------- tests -------------

    def test_add_quote_notification(self):
        self.add_quote(self.quote_minimal)
        reporter = User.query.all()[0]
        source = User.query.all()[1]
        self.assertEqual(Notification.query.filter_by(user_id=reporter.id).count(), 1) # reporter sent the notification
        self.assertEqual(Notification.query.filter_by(user_id=source.id).count(), 0) # and not the source

        notif = Notification.query.filter(Notification.recipients.any(User.id==source.id)).order_by(desc(Notification.id)).first()
        self.assertIsNotNone(notif) # source got the notif
        self.assert_is_same_notif(notif, {'user_id': reporter.id, 'type': 'quote', 'quote_id': 1, 'echo_id': 1}) # and it's correct

    def test_add_comment_notification(self):
        self.add_quote(self.quote_minimal)

        # source comment
        self.add_comment(self.comment_for_quote_one_again)
        reporter = User.query.all()[0]
        source = User.query.all()[1]
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==source.id), Notification.type=='comment').count(), 0) # source didn't get it b/c it's his comment
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==reporter.id), Notification.type=='comment').count(), 1) # reporter, however, got it

        notif = Notification.query.filter(Notification.recipients.any(User.id==reporter.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': source.id, 'type': 'comment', 'quote_id': 1, 'echo_id': 1}) # and it's correct
        
        # reporter comment
        self.add_comment(self.comment_for_quote_one)
        reporter = User.query.all()[0]
        source = User.query.all()[1]
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==source.id), Notification.type=='comment').count(), 1) # source got it
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==reporter.id), Notification.type=='comment').count(), 1) # reporter didn't get it b/c it's his comment

        notif = Notification.query.filter(Notification.recipients.any(User.id==source.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': reporter.id, 'type': 'comment', 'quote_id': 1, 'echo_id': 1}) # and it's correct

        # rando comment with no friends
        self.add_user(self.user_passive_spectator)
        self.add_comment(self.comment_for_one_by_passive)
        self.assertEqual(Notification.query.count(), 3) # nobody got a notification b/c rando is not friends w/ anyone

        # rando befriends reporter and source and comments again
        self.add_user(self.user_passive_spectator_with_friends)
        self.add_comment(self.comment_for_one_by_passive)
        reporter = User.query.all()[0]
        source = User.query.all()[1]
        rando = User.query.filter_by(fbid=self.user_passive_spectator_with_friends['id']).first()
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==source.id), Notification.type=='comment').count(), 2) # source got it this time
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==reporter.id), Notification.type=='comment').count(), 2) # so did reporter
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==rando.id)).count(), 0) # still nothing for poor rando

        notif = Notification.query.filter(Notification.recipients.any(User.id==source.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': rando.id, 'type': 'comment', 'quote_id': 1, 'echo_id': 1}) # and it's correct for source

        notif = Notification.query.filter(Notification.recipients.any(User.id==reporter.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': rando.id, 'type': 'comment', 'quote_id': 1, 'echo_id': 1}) # and for reporter

    def test_add_echo_notification(self):
        self.add_quote(self.quote_minimal)
        self.add_user(self.user_passive_spectator_with_friends)

        # echo
        self.add_echo("1", self.user_passive_spectator_with_friends['id'])
        reporter = User.query.all()[0]
        source = User.query.all()[1]
        rando = User.query.filter_by(fbid=self.user_passive_spectator_with_friends['id']).first()
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==source.id), Notification.type=='echo').count(), 1) # source got notified
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==reporter.id), Notification.type=='echo').count(), 1) # so did reporter
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==rando.id)).count(), 0) # still nothing for poor rando

        notif = Notification.query.filter(Notification.recipients.any(User.id==source.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': rando.id, 'type': 'echo', 'quote_id': 1, 'echo_id': 1}) # and it's correct for source

        notif = Notification.query.filter(Notification.recipients.any(User.id==reporter.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': rando.id, 'type': 'echo', 'quote_id': 1, 'echo_id': 1}) # and for reporter

    def test_add_fav_notification(self):
        self.add_quote(self.quote_minimal)
        self.add_user(self.user_passive_spectator_with_friends)

        # source favs
        self.add_fav("1", self.user_with_friends['id'])
        reporter = User.query.all()[0]
        source = User.query.all()[1]
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==source.id), Notification.type=='fav').count(), 0) # source didn't get it b/c it's his fav
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==reporter.id), Notification.type=='fav').count(), 1) # reporter, however, got it

        notif = Notification.query.filter(Notification.recipients.any(User.id==reporter.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': source.id, 'type': 'fav', 'quote_id': 1, 'echo_id': 1}) # and it's correct
        
        # reporter favs
        self.add_fav("1", self.user_simple['id'])
        reporter = User.query.all()[0]
        source = User.query.all()[1]
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==source.id), Notification.type=='fav').count(), 1) # source got it
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==reporter.id), Notification.type=='fav').count(), 1) # reporter didn't get it b/c it's his comment

        notif = Notification.query.filter(Notification.recipients.any(User.id==source.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': reporter.id, 'type': 'fav', 'quote_id': 1, 'echo_id': 1}) # and it's correct

        # rando favs
        self.add_fav("1", self.user_passive_spectator_with_friends['id'])
        reporter = User.query.all()[0]
        source = User.query.all()[1]
        rando = User.query.filter_by(fbid=self.user_passive_spectator_with_friends['id']).first()
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==source.id), Notification.type=='fav').count(), 2) # source got notified
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==reporter.id), Notification.type=='fav').count(), 2) # so did reporter
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==rando.id)).count(), 0) # still nothing for poor rando

        notif = Notification.query.filter(Notification.recipients.any(User.id==source.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': rando.id, 'type': 'fav', 'quote_id': 1, 'echo_id': 1}) # and it's correct for source

        notif = Notification.query.filter(Notification.recipients.any(User.id==reporter.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': rando.id, 'type': 'fav', 'quote_id': 1, 'echo_id': 1}) # and for reporter

    def test_add_notification_unicode(self):
        self.add_user(self.user_unicode_simple)

        # unicode user is source (and will be displayed in notification)
        self.add_quote(self.quote_unicode)

        reporter = User.query.filter_by(fbid=self.quote_unicode["reporterFbid"]).first()
        source = User.query.filter_by(fbid=self.quote_unicode["sourceFbid"]).first()
        self.assertEqual(Notification.query.filter_by(user_id=reporter.id).count(), 1) # reporter sent the notification

        notif = Notification.query.filter(Notification.recipients.any(User.id==source.id)).order_by(desc(Notification.id)).first()
        self.assertIsNotNone(notif) # source got the notif
        self.assert_is_same_notif(notif, {'user_id': reporter.id, 'type': 'quote', 'quote_id': 1, 'echo_id': 1}) # and it's correct

        # someone favorites it --> quote text is in notification text
        self.add_fav("1", self.user_simple['id'])
        reporter = User.query.filter_by(fbid=self.quote_unicode["reporterFbid"]).first()
        source = User.query.filter_by(fbid=self.quote_unicode["sourceFbid"]).first()
        rando = User.query.filter_by(fbid=self.user_simple['id']).first()
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==source.id), Notification.type=='fav').count(), 0) # source dit NOT get notified b/c he's not friends with the favver -- note that this functionality is independent from utf8 but we're not testing it separately b/c it might change
        self.assertEqual(Notification.query.filter(Notification.recipients.any(User.id==reporter.id), Notification.type=='fav').count(), 1) # so did reporter

        notif = Notification.query.filter(Notification.recipients.any(User.id==reporter.id)).order_by(desc(Notification.id)).first()
        self.assert_is_same_notif(notif, {'user_id': rando.id, 'type': 'fav', 'quote_id': 1, 'echo_id': 1}) # notif is correct for reporter

        # unicode user is reporter
        self.add_quote(self.quote_unicode_flipped) # unicode user is reporter

        reporter = User.query.filter_by(fbid=self.quote_unicode_flipped["reporterFbid"]).first()
        source = User.query.filter_by(fbid=self.quote_unicode_flipped["sourceFbid"]).first()
        self.assertEqual(Notification.query.filter_by(user_id=reporter.id).count(), 1) # reporter sent the notification

        notif = Notification.query.filter(Notification.recipients.any(User.id==source.id)).order_by(desc(Notification.id)).first()
        self.assertIsNotNone(notif) # source got the notif
        self.assert_is_same_notif(notif, {'user_id': reporter.id, 'type': 'quote', 'quote_id': 2, 'echo_id': 2}) # and it's correct

    def test_get_notifications(self):
        self.add_user(self.user_passive_spectator_with_friends)
        self.add_quote(self.quote_minimal)
        self.add_comment(self.comment_for_quote_one)
        self.add_echo("1", self.user_passive_spectator_with_friends['id'])
        self.add_fav("1", self.user_simple['id'])
        notifs_res = self.get_notifications(0, None, 0, self.user_with_friends['id'])
        self.assertEqual(len(notifs_res), 4) # we got all four

        notifs_res_expected = [
            {
                '_id': '1',
                'order_id': '1',
                'formatted-text': {
                    'text': 
                    '%s favorited your quote: "%s"' % (self.user_simple['name'], self.quote_minimal['quote']), 
                    'bold': [
                        {
                            'length': len(self.user_simple['name']),
                            'location': 0
                        }
                    ]
                },
                'unread': True,
                'type': 'fav'                
            },
            {
                '_id': '1',
                'order_id': '1',
                'formatted-text': {
                    'text': 
                    '%s echoed your quote: "%s"' % (self.user_passive_spectator['name'], self.quote_minimal['quote']), 
                    'bold': [
                        {
                            'length': len(self.user_passive_spectator['name']),
                            'location': 0
                        }
                    ]
                },
                'unread': True,
                'type': 'echo'
            },
            {
                '_id': '1',
                'order_id': '1',
                'formatted-text': {
                    'text': 
                    '%s commented on your quote.' % (self.user_simple['name']), 
                    'bold': [
                        {
                            'length': len(self.user_simple['name']),
                            'location': 0
                        }
                    ]
                },
                'unread': True,
                'type': 'comment'
            },
            {
                '_id': '1',
                'order_id': '1',
                'formatted-text': {
                    'text': 
                    '%s posted a quote by you!' % (self.user_simple['name']), 
                    'bold': [
                        {
                            'length': len(self.user_simple['name']),
                            'location': 0
                        }
                    ]
                },
                'unread': True,
                'type': 'quote'
            },
        ]

        for i in range(4):
            notif_res = self.get_notifications(1, 1, 1, self.user_with_friends['id'])[0]
            self.assertIn('timestamp', notif_res)
            del notif_res['timestamp'] # changes sometimes +- 1 sec
            self.assertEqual(notif_res, notifs_res_expected[i]) # extract them one by one and compare

    def test_set_notifprefs(self):
        # defaults
        self.set_notifprefs({}, self.user_simple['id'])
        user = User.query.first()
        self.assertEqual(user.notifprefs.quotes, 1)
        self.assertEqual(user.notifprefs.echoes, 1)
        self.assertEqual(user.notifprefs.comments, 1)
        self.assertEqual(user.notifprefs.favs, 1)

        # change some
        self.set_notifprefs({'quotes': 0, 'favs': 0}, self.user_simple['id'])
        user = User.query.first()
        self.assertEqual(user.notifprefs.quotes, 0)
        self.assertEqual(user.notifprefs.echoes, 1)
        self.assertEqual(user.notifprefs.comments, 1)
        self.assertEqual(user.notifprefs.favs, 0)

        # change others
        self.set_notifprefs({'echoes': 0, 'comments': 0}, self.user_simple['id'])
        user = User.query.first()
        self.assertEqual(user.notifprefs.quotes, 0)
        self.assertEqual(user.notifprefs.echoes, 0)
        self.assertEqual(user.notifprefs.comments, 0)
        self.assertEqual(user.notifprefs.favs, 0)

        # change all back
        self.set_notifprefs({'echoes': 1, 'comments': 1, 'quotes': 1, 'favs': 1}, self.user_simple['id'])
        user = User.query.first()
        self.assertEqual(user.notifprefs.quotes, 1)
        self.assertEqual(user.notifprefs.echoes, 1)
        self.assertEqual(user.notifprefs.comments, 1)
        self.assertEqual(user.notifprefs.favs, 1)

    def test_get_notifprefs(self):
        notifprefs = self.get_notifprefs(self.user_simple['id'])
        self.assertEqual(notifprefs, {'quotes': 1, 'favs': 1, 'comments': 1, 'echoes': 1}) # defaults

        user = User.query.first()
        user.notifprefs.quotes = 0
        user.notifprefs.comments = 0
        db.session.commit()
        notifprefs = self.get_notifprefs(self.user_simple['id'])
        self.assertEqual(notifprefs, {'quotes': 0, 'favs': 1, 'comments': 0, 'echoes': 1})

        user = User.query.first()
        user.notifprefs.echoes = 0
        user.notifprefs.favs = 0
        db.session.commit()
        notifprefs = self.get_notifprefs(self.user_simple['id'])
        self.assertEqual(notifprefs, {'quotes': 0, 'favs': 0, 'comments': 0, 'echoes': 0})

if __name__ == '__main__':
    unittest.main()
