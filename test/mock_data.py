# -*- coding: utf-8 -*-

class MockUserData():

    # these should be periodically updated from 
    # https://developers.facebook.com/apps/193862260739040/roles?role=test%20users
    fbids_tokens = {
        "100006678452194": "CAACwURMvyZBABAFwqrCSV60EHKlI8mxLZCvjX89KPZBGbECJ4dQ1YDHieUFBjngnV9F3Wmk5UZBwpZAcPpV8LNHSkcfVYTEats03zP9W7x8u0Pr7ykOa1qGyE8PZCzqbZByPHnk0UsYM8KOUemzlqjKGfZAWyvr7L5XX5l55J3WgDSbUSNkZCBxrE3X9eHObSTo0ZD",
        "100006629105407": "CAACwURMvyZBABAOXQZCL1F4A1CNNPZBVkgKMxYL8d7LrjFKbvBNhl1s1wZCZBabPfHOISfCWA6EN23CmiFIoa1C5jVSfIJDV7jGA0TwUqbFpNcBEivL82U6ZC0rV52QErcf3oiVAszZB9RZCr8wDio0xD0K63aTVkbDwZCdNT963dWYJ2rEX4BHqZCSaEZBZC5852IYZD",
        "100006546972451": "CAACwURMvyZBABAFf7NqE9IrRZBBcgofsHMKCpUg3xQSHzUQNZCEe3Xp44ZCZCCauhC1EjCIg9ScEefYXI3etbDeT8DqMXqzesxlRK9ZAgLnexAnj6H7BBnFqkuaVuwqxz2zZAVtcK0sgwWYsn8uCZCcLwJmURoZB1EBEVYfvWBFWcNZBJ1wKMGJZBFO2SVtq0C35GkZD",
        "100006688621903": "CAACwURMvyZBABAL6fhwnpRkN4dL5oFVhzAtBI9EKuGPk27pZAxa2I5eZAqqzQaHz3rZCuUD6ZCC1U5MOHWgoz0AoHYtAHhlBBmVBiBEuuePWJQsH8XTsWirqm8ug0iRe4cUgPqhq88ZBoRZAMq4JwpwazEW5cyUwHty55uecb3xV7rW8yqlRpZBuqlnahGp5J7AZD",
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

