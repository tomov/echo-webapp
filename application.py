import os
from flask import Flask, request
from model import db
from model import User, Quote, Echo, Comment
import json
from sqlalchemy import or_
import time

#----------------------------------------
# initialization
#----------------------------------------

application = Flask(__name__)  # Amazon Beanstalk bs
app = application              # ...and a hack around it

app.config.update(
    DEBUG = True,  # TODO (mom) remove before deploying
)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://ebroot:instaquote@aa1n9wwgoqy4mr8.cxexw98m36zh.us-east-1.rds.amazonaws.com/echo_webapp'

db.init_app(app)

#----------------------------------------
# controllers
#----------------------------------------

@app.route("/")
def hello():
    return "Hello from Python yay!"

# TODO (mom) add to utils.py
# TODO (mom) add unit tests
def split_name(name):
    names = name.split(" ")
    if len(names) == 0:
        return "", ""
    if len(names) == 1:
        return names[0], ""
    return names[0], names[len(names) - 1]


def add_friends(user, friends_raw):
    for friend_raw in friends_raw:
        friend_fbid = friend_raw['id']
        friend_first, friend_last = split_name(friend_raw['name'])
        friend_picture_url = friend_raw['picture']['data']['url']

        print 'add friend ' + friend_first + ' ' + friend_last + ' fbid = ' + friend_fbid

        friend = User.query.filter_by(fbid = friend_fbid).first()
        if not friend:
            friend = User(friend_fbid, None, friend_first, friend_last, friend_picture_url,  None, False)
            db.session.add(friend)
        user.friends.append(friend) # no worries, it's stored by reference in new_users_list


# TODO (mom) make secure (API keys?)
@app.route("/add_user", methods = ['POST'])
def add_user():
    udata = json.loads(request.form['data']) # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    fbid = udata['id']
    first_name, last_name = split_name(udata['name'])
    friends_raw = udata['friends']

    print 'CALL ADD USER WITH name = ' + first_name + ' ' + last_name
    print json.dumps(udata)

    user = User.query.filter_by(fbid = fbid).first()
    if not user:
        # user does not exist -- create one
        print "USER DOES NOT EXIST ==> CREATE ONE!"

        # TODO (mom) add picture URL
        # same with friends (note that picture url is already sent)
        user = User(fbid, udata['email'], first_name, last_name, None, None, True)

        # TODO (mom) do this in separate thread http://stackoverflow.com/questions/2882308/spawning-a-thread-in-python
        add_friends(user, friends_raw)

        # or even better -- use Amazon SQS ?
        print ' db session add'
        db.session.add(user)

    elif user.registered == False:
        print "USER EXISTS BUT NOT REGISTERED -- REGISTER HER!"

        user.registered = True
        add_friends(user, friends_raw) # TODO sep thread?

        # TODO (mom) update friend list as well -- http://stackoverflow.com/questions/6611563/sqlalchemy-on-duplicate-key-update
    else:
        print "USER REGISTERED -- ABORT"
        return "user already registered"

    print ' db session commit'
    db.session.commit()
    print ' db done!'

    return 'user added maybe?'
 

@app.route("/add_quote", methods = ['POST'])
def add_quote():
    qdata = json.loads(request.form['data'])
    sourceFbid = qdata['sourceFbid']
    reporterFbid = qdata['reporterFbid']
    location = qdata['location']
    content = qdata['quote']

    source = User.query.filter_by(fbid = sourceFbid).first()
    reporter = User.query.filter_by(fbid = reporterFbid).first()

    if not source:
        return 'source with fbid %r not found' % sourceFbid
    if not reporter:
        return 'reporter with fbid %r not found' % reporterFbid

    quote = Quote(source.id, reporter.id, content, location, False)
    db.session.add(quote)
    print 'db commit quote'
    db.session.commit()
    print 'db commited!'

    return 'quote added maybe?' 


@app.route("/get_quotes", methods = ['get'])
def get_quotes():
    fbid = request.args.get('fbid')

    print 'start getting quotes for ' + fbid

    user = User.query.filter_by(fbid = fbid).first()
    if not user:
        return 'User NOT signed up'

    #or_conds = [or_(Quote.sourceId = friend.id, Quote.reporterId = friend.id) for friend in user.friends]
    #or_conds.append(or_(Quote.sourceId = user.id, Quote.reporterId = user.id))
   
    print 'fetching quotes for ids'

    ids = [friend.id for friend in user.friends]
    ids.append(user.id)
    quotes = Quote.query.filter(or_(Quote.source_id.in_(ids), Quote.reporter_id.in_(ids))).all()

    print 'fetched %d quotes' % len(quotes)

    result = []
    for quote in quotes:
        # TODO (mom/rishi) coordinate field type and naming convention
        quote_res = dict()
        quote_res['_id'] = str(quote.id)
        quote_res['timestamp'] = time.mktime(quote.created.timetuple()) # doesn't jsonify
        quote_res['sourceFbid'] = quote.source.fbid
        quote_res['reporterFbid'] = quote.reporter.fbid
        quote_res['location'] = quote.location
        quote_res['quote'] = quote.content
        result.append(quote_res)

    sorted_result = sorted(result, key = lambda k: k['timestamp'], reverse=True)
    print sorted_result
    try:
        dump = json.dumps(sorted_result)
        return dump
    except:
        return "fail... couldn't json dump"


#----------------------------------------
# launch
#----------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
