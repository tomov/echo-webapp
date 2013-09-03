import base
from base import *
import api_helpers
from api_helpers import *
import mock_data
from mock_data import *

from model import Echo

class TestEchoAPI(TestBase, EchoAPIHelpers, MockUserData, MockQuoteData):

    def setUp(self):
        TestBase.setUp(self)
        self.add_user(self.user_passive_spectator)
        self.add_user(self.user_unicode_simple)
        self.add_user(self.user_simple)
        self.add_user(self.user_with_friends)
        self.add_quote(self.quote_minimal)
        self.add_quote(self.quote_normal)

    # ------------- helpers -------------

    # see if favs_res = get_favs(...) for a quote corresponds to the array user_ids_expected
    def assert_are_same_echoers(self, echoers_res, user_ids_expected):
        echoers_dicts = []
        for user_id in user_ids_expected:
            user = User.query.filter_by(id=user_id).first()
            self.assertIsNotNone(user)
            echoer_dict = {
                "fbid": user.fbid,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
            echoers_dicts.append(echoer_dict)
        self.assertItemsEqual(echoers_res, echoers_dicts)

    # ------------- tests -------------

    def test_add_echo(self):
        self.add_echo("1", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.filter_by(quote_id=1, user_id=1).count(), 1) # added
        self.assertEqual(Echo.query.filter_by(quote_id=1).count(), 2) # in addition to default echo

        user = User.query.first()
        quote = Quote.query.first()
        self.assertIn(quote, user.echoes)
        self.assertIn(user, quote.echoers)

    def test_add_echo_invalid(self):
        self.add_echo("1", "invalid")
        self.assertEqual(Echo.query.count() - Quote.query.count(), 0) # invalid user

        self.add_echo("invalid", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 0) # invalid quote

        quote = Quote.query.first()
        quote.deleted = True
        db.session.commit()
        self.add_echo("1", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 0) # quote deleted

        quote = Quote.query.first()
        quote.deleted = False
        db.session.commit()
        self.add_echo("1", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # added
        self.add_echo("1", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # duplicate ignored

        self.add_echo("1", self.user_simple['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # source cannot echo
        self.add_echo("1", self.user_with_friends['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # reporter cannot echo either

    def test_delete_echo(self):
        self.add_echo("1", self.user_passive_spectator['id'])

        self.delete_echo("1", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 0) # deleted

        self.add_echo("1", self.user_passive_spectator['id'])
        self.add_echo("1", self.user_unicode_simple['id'])
        self.assertEqual(Echo.query.filter_by(quote_id=1).count() - 1, 2) # re-add deleted echo

        self.delete_echo("1", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.filter_by(quote_id=1).count() - 1, 1) # selective delete
        quote = Quote.query.first()
        self.assertEqual(quote.echoers[1].id, 2) # second echoer remained

        self.delete_echo("1", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.filter_by(quote_id=1).count() - 1, 1) # repeat delete ignored

    def test_delete_fav_invalid(self):
        self.add_echo("1", self.user_passive_spectator['id'])

        self.delete_echo("1", "invalid")
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # invalid user

        self.delete_echo("invalid", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # invalid quote

        quote = Quote.query.first()
        quote.deleted = True
        db.session.commit()
        self.delete_echo("1", self.user_passive_spectator['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # quote deleted

        quote = Quote.query.first()
        quote.deleted = False
        db.session.commit()
        self.delete_echo("1", self.user_unicode_simple['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # you must have echoed to remove an echo
        self.delete_echo("1", self.user_simple['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # source cannot delete echo
        self.delete_echo("1", self.user_with_friends['id'])
        self.assertEqual(Echo.query.count() - Quote.query.count(), 1) # reporter cannot delete echo either

    def test_get_echoers(self):
        self.add_echo("1", self.user_passive_spectator['id'])
        self.add_echo("1", self.user_unicode_simple['id'])
        self.add_echo("2", self.user_passive_spectator['id'])

        echoers_res = self.get_echoers("1", self.user_simple['id'])
        self.assert_are_same_echoers(echoers_res, [1, 2])
        echoers_res = self.get_echoers("2", self.user_simple['id'])
        self.assert_are_same_echoers(echoers_res, [1])


if __name__ == '__main__':
    unittest.main()