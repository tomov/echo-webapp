# -*- coding: utf-8 -*-

## Note that if you change these, you will have to change some of the assertions in application_test.py
## specifically, look for the word "hardcoded"

class RandomUsers:
    george = {
        "id": "100002537919668",
        "email": "myrzi.me@gmail.com",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc7/370214_100000486204833_1328204472_q.jpg",
        "name": "George Tomov", 
        "friends": [
            {
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/203434_703951380_2070708925_q.jpg", 
                        "is_silhouette": False
                    }
                }, 
                "id": "703951380", 
                "name": "Angela Pinkerton"
            },
            {
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc6/274340_1778127543_1201810974_q.jpg",
                        "is_silhouette": False
                    }
                }, 
                "id": "1778127543", 
                "name": "Michele Alex"
            },
            {
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc6/275685_100001040617130_24180076_q.jpg",
                        "is_silhouette": False
                    }
                }, 
                "id": "100001040617130", 
                "name": "Momchil's Mom"
            },
            {
                "picture": {
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/370322_100002571158857_1251482889_q.jpg",
                        "is_silhouette": False
                    }
                }, 
                "id": "100002571158857", 
                "name": "Deepika Narang"
            },
        ]
    }


    deepika = {
        "id": "100002571158857", 
        "email": "notherrealemail@gmail.com",
        "name": "Deepika Narang",
        "picture_url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/370322_100002571158857_1251482889_q.jpg",
        "friends": [
            {
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc7/370214_100000486204833_1328204472_q.jpg",
                        "is_silhouette": False
                    }
                }, 
                "id": "100002537919668",
                "name": "George Tomov"
            },
        ]
    }


    angela = {
        "id": "703951380",
        "email": "angela@gmail.com",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/203434_703951380_2070708925_q.jpg",
        "name": "Angela Pinkerton", 
        "friends": [
            {
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc7/370214_100000486204833_1328204472_q.jpg",
                        "is_silhouette": False
                    }
                }, 
                "id": "100002537919668", 
                "name": "George Tomov"
            },
            {
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc6/274340_1778127543_1201810974_q.jpg",
                        "is_silhouette": False
                    }
                }, 
                "id": "1778127543", 
                "name": "Michele Alex"
            },
            {
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-prn1/157595_100002370439632_748462517_q.jpg",
                        "is_silhouette": False
                    }
                }, 
                "id": "1304316688", 
                "name": "Cameron Livingston"
            },
            {
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-prn1/274070_100002505656933_2199345_q.jpg",
                        "is_silhouette": False
                    }
                }, 
                "id": "100002505656933", 
                "name": "Zdravko Beshev"
            },
        ]
    }


    zdravko = {
        "id": "100002505656933",
        "email": "zdravko@gmail.com",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-prn1/274070_100002505656933_2199345_q.jpg",
        "name": "Zdravko Beshev", 
        "friends": [
            {
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/203434_703951380_2070708925_q.jpg",
                        "is_silhouette": False
                    }
                }, 
                "id": "703951380",
                "name": "Angela Pinkerton"
            },
        ]
    }


    lili = {
        "id": "1234567",
        "email": "lili@gmail.com",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-prn1/274070_100002505656933_2199345_q.jpg",
        "name": "Lili Driggs", 
        "friends": [
            {
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/203434_703951380_2070708925_q.jpg",
                        "is_silhouette": False
                    }
                }, 
                "id": "7654321",
                "name": "Mimi Hello"
            },
        ]
    }


    mimi = {
        "id": "7654321",
        "email": "mimi@gmail.com",
        "picture_url": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/203434_703951380_2070708925_q.jpg", 
        "name": "Mimi Hello", 
        "friends": [
            {
                "picture": { 
                    "data": {
                        "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-prn1/274070_100002505656933_2199345_q.jpg",
                        "is_silhouette": False
                    }
                }, 
                "id": "1234567",
                "name": "Lili Driggs"
            },
        ]
    }



class RandomStuff:
    not_friends_with_george = [
        {
            "picture": { 
                "data": {
                    "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-prn1/157595_100002370439632_748462517_q.jpg",
                    "is_silhouette": False
                }
            }, 
            "id": "1304316688", 
            "name": "Cameron Livingston"
        },
        {
            "picture": { 
                "data": {
                    "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-prn1/274070_100002505656933_2199345_q.jpg",
                    "is_silhouette": False
                }
            }, 
            "id": "100002505656933", 
            "name": "Zdravko Beshev"
        },
        {
            "picture": { 
                "data": {
                    "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/203434_703951380_2070708925_q.jpg",
                    "is_silhouette": False
                }
            }, 
            "id": "7654321",
            "name": "Mimi Hello"
        },
    ]

    not_friends_with_angela = [
        {
            "picture": { 
                "data": {
                    "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-snc6/275685_100001040617130_24180076_q.jpg",
                    "is_silhouette": False
                }
            }, 
            "id": "100001040617130", 
            "name": "Momchil's Mom"
        },
        {
            "picture": {
                "data": {
                    "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/370322_100002571158857_1251482889_q.jpg",
                    "is_silhouette": False
                }
            }, 
            "id": "100002571158857", 
            "name": "Deepika Narang"
        },
        {
            "picture": { 
                "data": {
                    "url":"https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/203434_703951380_2070708925_q.jpg",
                    "is_silhouette": False
                }
            }, 
            "id": "7654321",
            "name": "Mimi Hello"
        },
    ]



class RandomQuotes:
    contemporary_art = {
        "location": "Museum of Modern Art",
        "location_lat": 23423453.34352,
        "location_long": 3465435642.45,
        "quote": "Contemporary art is like unicorns run over by tanks",
        "reporterFbid": 100002537919668, # george
        "sourceFbid": 703951380  # angela
    }
    girlfriend = {
        "location": "Joline Hall",
        "location_lat": 99923453.34352,
        "location_long": 12435642.45,
        "quote": "Wait, that's his girlfriend? I thought it was weird that he was touching her face...",
        "reporterFbid": 703951380, # angela
        "sourceFbid": 100002537919668  # geroge
    }
    anotherquote = {
        "location": "Princeton, NJ",
        "location_lat": 234235.34352,
        "location_long": 311115642.45,
        "quote": "Is this really a quote? So meta...",
        "reporterFbid": 703951380, # angela 
        "sourceFbid": 1304316688  # cameron (unregistered)
    }
    andanotherone = {
        "location": "Unknown location",
        "location_lat": 2343.34352,
        "location_long": 34642.45,
        "quote": "This is really super meta.... unreal... lkasdjfljasldfkj",
        "reporterFbid": 100002571158857, # deepika
        "sourceFbid": 100002537919668 # george
    }


class RandomComments:
    thissucks = {
        "quoteId": 1,
        "userFbid": 703951380, # angela
        "comment": "this quote sucks"
    }
    funnyquote = {
        "quoteId": 1,
        "userFbid": 100002571158857, # deepika
        "comment": "LOL this quote is truly hilarious!"
    }
    angelayousuck = {
        "quoteId": 1,
        "userFbid": 100002505656933, # zdravko
        "comment": "Angela you suck!"
    }

