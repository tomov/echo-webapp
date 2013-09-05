# -*- coding: utf-8 -*-

class MockUserData():

    # these should be periodically updated from 
    # https://developers.facebook.com/apps/193862260739040/roles?role=test%20users
    fbids_tokens = {
        "100006678452194": "CAACwURMvyZBABADuZCOYmDSxwaSLX2ZAsGTnQ7wvOobjwBOJ2cGU4ZBH2bSwIiIznphZA4qsh8NmUbWzCVZAZAaOu7vfxvtVrkEZAgip37rEXVxZCd9ChWAaRPQ0bxkeffwm4YZCIkg5ZAAUcXaNLEdwZCb6nKUZCaO18NX75nDZAZApMs4ZCEuGi1GtyvZA4K2hjfiVoSnIZD",
        "100006629105407": "CAACwURMvyZBABAHY0n4SrYQ3xGpoxVOSNWzDjwFuHYTWTcZC0ZCJJAu3IjXzH3B043Ff9XZCJE6hWSU7GHr1TgzGaiGZAIGjzQzqt2FnndZCdTTO6TucJRoSQ2Cc2CF3WeziX365p7q57WNhZCRLi06Ix2qhEtSoXZB68Df0Bd0TVzGNR58IDc6TIpajgdbMWT8ZD",
        "100006546972451": "CAACwURMvyZBABAJmeqfIioB62Ul1ZAPNttkCz3hyXvkHNCiNZCwX03duE7Q6fWwDGL7TMFB9GFZCABZBtERxP4OElvK7GjijPFJjEqwy3hV2EfToZATzKip5Ph8B4dHBK7lineBXbG5KK8MDWu3wGk14WkqIQ2D8IZBZAR2BBZAmOZCObQsdBKQiqdVdrnH0jqZC8YZD",
        "100006688621903": "CAACwURMvyZBABAFHTBNyAbvsxRgYuZAb3J76IXiALS0ynmVPLFVYpKvnjHg6ZB1rQS4lG2i5ZAkJR89LaVdUbpNMvpii5uLxUGjCZAnCghFdMLTvQNfokZB8PKxfLGuw7FZCCEEmKPDqfC02BXk96HZC1hmdFxZBFSXzZAvzN1nTtkRlmsSONZC09mmi29Tte4Lt5YZD",
    }

    user_simple = {
        "id": "100006629105407",
        "email": "khrfkvs_wisemanescu_1378106137@tfbnw.net",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc7/370214_100000486204833_1328204472_q.jpg",
        "name": "Helen Wisemanescu", 
        "friends": [],
        "unfriends": []
    }

    user_with_friends = {
        "id": "100006546972451",
        "email": "gwncgzh_greenestein_1378106136@tfbnw.net",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc6/274340_1778127543_1201810974_q.jpg",
        "name": "Elizabeth Greenestein", 
        "friends": [
            {
                "id": user_simple['id'],
                "name": user_simple['name'],
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/203434_703951380_2070708925_q.jpg"
                    }
                }, 
            },
            {
                "id": "1778127543", 
                "name": "Michele Alex",
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/370322_100002571158857_1251482889_q.jpg"
                    }
                }, 
            },
            {
                "id": "100001040617130", 
                "name": "Momchil's Mom",
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc6/275685_100001040617130_24180076_q.jpg"
                    }
                }, 
            },
        ],
        "unfriends": []
    }

    # see HARDCODED below if you change this guy
    user_with_friends_update = {
        "id": user_with_friends['id'],
        "email": "new_email@gmail.com",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc6/274340_1778127543_1201810974666666.jpg",
        "name": user_with_friends['name'],
        "friends": [
            {
                "id": user_simple['id'],
                "name": user_simple['name'],
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/203434_703951380_2070708925_q.jpg"
                    }
                }, 
            },
            {
                "id": "11324123412341234", 
                "name": "Somebody New",
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/203434_703951380_20707089251111_q.jpg"
                    }
                }, 
            }
        ],
        "unfriends": [user_with_friends['friends'][1]['id'], user_with_friends['friends'][2]['id'], "invalid"]
    }

    user_unicode_simple = {
        "id": "100006688621903",
        "email": "mknoabj_mcdonaldsen_1378106135@tfbnw.net",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc7/370214_100000486204833_1328204472_qq123.jpg",
        "name": "Дейв МакДоналдсън",
        "friends": [],
        "unfriends": []
    }

    user_invalid_fbid = {
        "id": "invalid",
        "email": "khrfkvs_wisemanescu_1378106137@tfbnw.net",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc7/370214_100000486204833_1328204472_q.jpg",
        "name": "Helen Wisemanescu", 
        "friends": [],
        "unfriends": []
    }

    user_passive_spectator = {
        "id": "100006678452194",
        "email": "random@gmail.com",
        "picture_url": "https://there-is-no-such-url/1328204472_q.jpg",
        "name": "Donna Shepardwitz", 
        "friends": [],
        "unfriends": []
    }

    user_passive_spectator_with_friends = {
        "id": user_passive_spectator['id'],
        "email": user_passive_spectator['email'],
        "picture_url": user_passive_spectator['picture_url'],
        "name": user_passive_spectator['name'],
        "friends": [
            {
                "id": user_simple['id'],
                "name": user_simple['name'],
                "picture": { 
                    "data": {
                        "url": user_simple['picture_url']
                    }
                }, 
            },
            {
                "id": user_with_friends['id'],
                "name": user_with_friends['name'],
                "picture": { 
                    "data": {
                        "url": user_with_friends['picture_url']
                    }
                }, 
            }
        ],
        "unfriends": []
    }


class MockQuoteData():

    quote_minimal = {
        "quote": "Here's to the crazy ones. The misfits. The rebels. The troublemakers. The round pegs in the square holes.",
        "reporterFbid": MockUserData.user_simple['id'],
        "sourceFbid": MockUserData.user_with_friends['id']
    }

    quote_minimal_flipped = {
        "quote": "Here's to the round pegs in the square holes. The troublemakers. The rebels. The misfits. The crazy ones.",
        "reporterFbid": MockUserData.user_with_friends['id'],
        "sourceFbid": MockUserData.user_simple['id']
    }

    quote_normal = {
        "location": "Randomtown, USA",
        "location_lat": 2343.34352,
        "location_long": 34642.45,
        "quote": "This is a sample quote with no particular entertainment value.",
        "reporterFbid": MockUserData.user_simple['id'],
        "sourceFbid": MockUserData.user_with_friends['id']
    }

    quote_unicode = {
        "quote": "От една страна си ебало майката, от друга страна майката си ебало!!!",
        "reporterFbid": MockUserData.user_with_friends['id'],
        "sourceFbid": MockUserData.user_unicode_simple['id']
    }

    quote_unicode_flipped = {
        "quote": "От една страна майката си ебало, от друга страна си ебало майката!!!",
        "reporterFbid": MockUserData.user_unicode_simple['id'],
        "sourceFbid": MockUserData.user_with_friends['id']
    }

    quote_invalid_source = {
        "quote": "Here's to the crazy ones. The misfits. The rebels. The troublemakers. The round pegs in the square holes.",
        "reporterFbid": MockUserData.user_simple['id'],
        "sourceFbid": "invalid"
    }

    quote_invalid_reporter = {
        "quote": "Here's to the crazy ones. The misfits. The rebels. The troublemakers. The round pegs in the square holes.",
        "reporterFbid": "invalid",
        "sourceFbid": MockUserData.user_with_friends['id']
    }

    quote_same_source_reporter = {
        "quote": "The inability to quote yourself removes the narcissistic element from Echo, ensuring all of our content is original, spontaneous, honest, and funny",
        "reporterFbid": MockUserData.user_simple['id'],
        "sourceFbid": MockUserData.user_simple['id']
    }

    quote_normal_two = {
        "location": "Princeton, NJ",
        "location_lat": 23.342,
        "location_long": 364.41,
        "quote": "Echo is just another social mobile local iPhone app.",
        "reporterFbid": MockUserData.user_passive_spectator['id'],
        "sourceFbid": MockUserData.user_with_friends['id']
    }


class MockCommentData():

    comment_for_quote_one = {
        "userFbid": MockUserData.user_simple['id'],
        "quoteId": "1",
        "comment": "Hahaha this is sooo true!! lol"
    }

    comment_for_quote_one_again = {
        "userFbid": MockUserData.user_with_friends['id'],
        "quoteId": "1",
        "comment": "Seconded!"
    }

    comment_for_quote_two = {
        "userFbid": MockUserData.user_simple['id'],
        "quoteId": "2",
        "comment": "This is for a different quote"
    }

    comment_for_one_by_passive = {
        "userFbid": MockUserData.user_passive_spectator['id'],
        "quoteId": "1",
        "comment": "This is from a user that's not the source nor the reporter"
    }

    comment_invalid_quote = {
        "userFbid": MockUserData.user_simple['id'],
        "quoteId": "invalid",
        "comment": "This is for an invalid quote id"
    }

    comment_unicode = {
        "userFbid": MockUserData.user_unicode_simple['id'],
        "quoteId": "1",
        "comment": "Айде един и на български"
    }

