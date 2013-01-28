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


# TODO (mom) make secure (API keys?)
@app.route("/add_user", methods = ['POST'])
def add_user():
    udata = json.loads(request.form['data']) # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    fbid = udata['id']
    # print 'fbid = ' + fbid #: can't concatenate str and int
    friends_raw = udata['friends']
    name = udata['name']
    names = name.split(" ")
    first_name = names[0]
    last_name = names[len(names) - 1]
    print 'name = ' + name

    # TODO (mom) add picture URL and load picture in background thread
    # same with friends (note that picture url is already sent)
    user = User(fbid, udata['email'], first_name, last_name, None, None, True)

    if User.query.filter_by(fbid = fbid).first():
        return 'user already exists' # TODO (mom) update friend list in this case -- http://stackoverflow.com/questions/6611563/sqlalchemy-on-duplicate-key-update

    # TODO (mom) do this in separate thread http://stackoverflow.com/questions/2882308/spawning-a-thread-in-python
    # or even better -- use Amazon SQS ?
    for friend_raw in friends_raw:
        friend_fbid = friend_raw['id']
        print friend_fbid + ' <---- fbid one'
        friend = User.query.filter_by(fbid = friend_fbid).first()
        if not friend:
            friend = User(friend_fbid)
            db.session.add(friend)
        user.friends.append(friend) # no worries, it's stored by reference in new_users_list

    print ' db session add'
    db.session.add(user)
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
    app.run(host='0.0.0.0', port=port)
