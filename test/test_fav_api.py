import base
from base import *
import api_helpers
from api_helpers import *
import mock_data
from mock_data import *

from model import Favorite

class TestFavAPI(TestBase, FavAPIHelpers, MockUserData, MockQuoteData):

    def setUp(self):
        TestBase.setUp(self)
        self.add_user(self.user_simple)
        self.add_user(self.user_with_friends)
        self.add_user(self.user_unicode_simple)
        self.add_quote(self.quote_minimal)
        self.add_quote(self.quote_normal)

    # ------------- helpers -------------

    # see if favs_res = get_favs(...) for a quote corresponds to the array user_ids_expected
    def assert_are_same_favs(self, favs_res, user_ids_expected):
        favs_dicts = []
        for user_id in user_ids_expected:
            user = User.query.filter_by(id=user_id).first()
            self.assertIsNotNone(user)
            fav_dict = {
                "fbid": user.fbid,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
            favs_dicts.append(fav_dict)
        self.assertItemsEqual(favs_res, favs_dicts)

    # ------------- tests -------------

    def test_add_fav(self):
        self.add_fav("1", self.user_simple['id'])
        self.assertEqual(Favorite.query.filter_by(quote_id=1, user_id=1).count(), 1) # added

        favorite = Favorite.query.first()
        user = User.query.first()
        quote = Quote.query.first()
        self.assertIn(favorite, user.favs) # added to user
        self.assertIn(favorite, quote.favs) # and to quote

    def test_add_fav_invalid(self):
        self.add_fav("1", "invalid")
        self.assertEqual(Favorite.query.count(), 0) # invalid user

        self.add_fav("invalid", self.user_simple['id'])
        self.assertEqual(Favorite.query.count(), 0) # invalid quote

        quote = Quote.query.first()
        quote.deleted = True
        db.session.commit()
        self.add_fav("1", self.user_simple['id'])
        self.assertEqual(Favorite.query.count(), 0) # quote deleted

        quote = Quote.query.first()
        quote.deleted = False
        db.session.commit()
        self.add_fav("1", self.user_simple['id'])
        self.assertEqual(Favorite.query.count(), 1) # added
        self.add_fav("1", self.user_simple['id'])
        self.assertEqual(Favorite.query.count(), 1) # duplicate ignored


    def test_delete_fav(self):
        self.add_fav("1", self.user_simple['id'])

        self.delete_fav("1", self.user_simple['id'])
        self.assertEqual(Favorite.query.count(), 0) # deleted

        self.add_fav("1", self.user_simple['id'])
        self.add_fav("1", self.user_with_friends['id'])
        self.assertEqual(Favorite.query.filter_by(quote_id=1).count(), 2) # re-add deleted fav

        self.delete_fav("1", self.user_simple['id'])
        self.assertEqual(Favorite.query.filter_by(quote_id=1).count(), 1) # selective delete
        quote = Quote.query.first()
        self.assertEqual(quote.favs[0].user_id, 2) # second fav remained

        self.delete_fav("1", self.user_simple['id'])
        self.assertEqual(Favorite.query.filter_by(quote_id=1).count(), 1) # repeat delete ignored

    def test_delete_fav_invalid(self):
        self.add_fav("1", self.user_simple['id'])

        self.delete_fav("1", "invalid")
        self.assertEqual(Favorite.query.count(), 1) # invalid user

        self.delete_fav("invalid", self.user_simple['id'])
        self.assertEqual(Favorite.query.count(), 1) # invalid quote

        quote = Quote.query.first()
        quote.deleted = True
        db.session.commit()
        self.delete_fav("1", self.user_simple['id'])
        self.assertEqual(Favorite.query.count(), 1) # quote deleted

        quote = Quote.query.first()
        quote.deleted = False
        db.session.commit()
        self.delete_fav("1", self.user_passive_spectator['id'])
        self.assertEqual(Favorite.query.count(), 1) # user hasn't favorited that quote

    def test_get_favs(self):
        self.add_fav("1", self.user_simple['id'])
        self.add_fav("1", self.user_with_friends['id'])
        self.add_fav("2", self.user_simple['id'])

        favs_res = self.get_favs("1", self.user_simple['id'])
        self.assert_are_same_favs(favs_res, [1, 2])
        favs_res = self.get_favs("2", self.user_simple['id'])
        self.assert_are_same_favs(favs_res, [1])


if __name__ == '__main__':
    unittest.main()