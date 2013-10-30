# -*- coding: utf-8 -*-

import base
from base import *
import api_helpers
from api_helpers import *
import mock_data
from mock_data import *
from util import *

class TestUserAPI(TestBase, UserAPIHelpers, MockUserData):

    # ------------- helpers -------------

    # check if db entry user after add_user(user_dict) is the same as user_dict
    def assert_is_same_user_simple(self, user, user_dict):
        self.assertIsNotNone(user)
        self.assertTrue(user.registered)
        self.assertEqual(user.email, user_dict['email'].decode('utf-8'))
        self.assertEqual(user.picture_url, user_dict['picture_url'])
        self.assertEqual(user.fbid, user_dict['id'])
        first, last = split_name(user_dict['name'].decode('utf-8'))
        self.assertEqual(user.first_name, first.decode('utf-8'))
        self.assertEqual(user.last_name, last.decode('utf-8'))
        self.assertEqual(len(user.all_friends), len(user_dict['friends']))

    # same as above but also checks for friends
    def assert_is_same_user_with_friends(self, user, user_dict):
        self.assert_is_same_user_simple(user, user_dict)
        all_friends_dicts = []
        for friend in user.all_friends:
            friend_dict = {
                u"id": friend.fbid,
                u"name": friend.first_name + " " + friend.last_name,
                u"picture": {
                    u"data": {
                        u"url": friend.picture_url
                    }
                }
            }
            all_friends_dicts.append(friend_dict)
        # convert to unicode -- makes comparison easier
        user_dict_friends_unicode = []
        for i in range(len(user_dict['friends'])):
            unidict = dict_to_unicode_dict(user_dict['friends'][i])
            user_dict_friends_unicode.append(unidict)
        self.assertItemsEqual(all_friends_dicts, user_dict_friends_unicode)

    # make sure every friend of user also has user as a friend
    def assert_friends_reciprocity(self, user):
        self.assertIsNotNone(user)
        for friend in user.all_friends:
            self.assertTrue(user in friend.all_friends)

    # ------------- tests -------------

    def testget_token(self):
        token = self.get_token_for_user_with_fbid(self.user_simple['id'])
        self.assertEqual(User.query.count(), 1) # hollow profile is created

    def test_get_token_invalid(self):
        token = self.get_token_for_user_with_fbid("invalid")
        self.assertEqual(User.query.count(), 0) # no hollow profile is created

    def test_add_user_simple(self):
        self.add_user(self.user_simple)
        self.assertEqual(User.query.count(), 1) # user info is updated (no new user is created)

        user = User.query.first()
        self.assert_is_same_user_simple(user, self.user_simple)

    def test_add_user_simple_invalid(self):
        self.add_user(self.user_invalid_fbid)
        self.assertEqual(User.query.count(), 0) # no user is created

    def test_add_user_with_friends(self):
        self.add_user(self.user_with_friends)
        self.assertEqual(User.query.count(), 1 + len(self.user_with_friends['friends'])) # friends are added as users

        user = User.query.first()
        self.assert_is_same_user_with_friends(user, self.user_with_friends) # user and friend data is ok
        self.assert_friends_reciprocity(user) # friend relationships are symmetrical

    def test_add_user_with_friends_extended(self):
        self.add_user(self.user_simple)
        self.add_user(self.user_with_friends)
        self.assertEqual(User.query.count(), 1 + len(self.user_with_friends['friends'])) # existing friend is not duplicated

        user = User.query.filter_by(fbid=self.user_with_friends['id']).first()
        self.assert_is_same_user_with_friends(user, self.user_with_friends) # existing friend picture_url is updated
        self.assert_friends_reciprocity(user) # existing friend knows about new user

        self.add_user(self.user_with_friends_update)
        self.assertEqual(User.query.count(), 1 + len(self.user_with_friends['friends']) + 1) # HARDCODED + 1 user -- one new friend and new user

        user = User.query.filter_by(fbid=self.user_with_friends_update['id']).first()
        self.assert_is_same_user_with_friends(user, self.user_with_friends_update) # friends and data is updated. Notice one friend is duplicate and one unfriend is non-existing
        self.assert_friends_reciprocity(user) # new relationship is symmetrical

        for user in User.query.all(): # unfriends are unfriended and it's symmetrical, also HARDCODED
            if user.fbid != self.user_with_friends_update['id']:
                if user.fbid in self.user_with_friends_update['unfriends']:
                    self.assertEqual(len(user.all_friends), 0)
                else:
                    self.assertEqual(len(user.all_friends), 1)

        user_with_friends_refresh_friendlist = self.user_with_friends
        user_with_friends_refresh_friendlist['refreshing_entire_friend_list'] = 1
        self.add_user(user_with_friends_refresh_friendlist)
        user = User.query.filter_by(fbid=self.user_with_friends['id']).first()
        self.assert_is_same_user_with_friends(user, self.user_with_friends) # friend list is refreshed entirely (i.e. back to the original one; all new friendships are forgotten)

    def test_add_user_unicode(self):
        self.add_user(self.user_unicode_simple)
        self.assertEqual(User.query.count(), 1) # user added

        user = User.query.first()
        self.assert_is_same_user_simple(user, self.user_unicode_simple)

    def test_register_token_simple(self):
        self.add_user(self.user_simple)
        device_token = 'some_random_device_token'

        # register token
        self.register_device_token({'token': device_token}, self.user_simple['id'])
        user = User.query.first()
        self.assertEqual(user.device_token, device_token) # token updated successfully

        # unregister token
        self.register_device_token({'token': None}, self.user_simple['id'])
        user = User.query.first()
        self.assertIsNone(user.device_token) # token deleted successfully

    def test_register_token_duplicate(self):
        self.add_user(self.user_simple)
        self.add_user(self.user_with_friends)
        device_token = 'some_random_device_token'
        self.register_device_token({'token': device_token}, self.user_simple['id'])
        self.register_device_token({'token': device_token}, self.user_with_friends['id'])

        user = User.query.filter_by(fbid=self.user_simple['id']).first()
        self.assertEqual(user.device_token, device_token) # token updated successfully for first user

        user = User.query.filter_by(fbid=self.user_with_friends['id']).first()
        self.assertIsNone(user.device_token) # but not for second user


if __name__ == '__main__':
    unittest.main()