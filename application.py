import os
from flask import Flask, request
from model import db
from model import User # TODO (mom) import one by one? or all at once
import json

#----------------------------------------
# initialization
#----------------------------------------

application = Flask(__name__)  # Amazon Beanstalk bs
app = application              # ...and a hack around it

app.config.update(
    DEBUG = True,  # TODO (mom) remove before deploying
)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://ebroot:instaquote@aa1ame3lqpnmuv0.clozqiwggjtt.us-east-1.rds.amazonaws.com/echo_webapp'

db.init_app(app)

#----------------------------------------
# controllers
#----------------------------------------

@app.route("/")
def hello():
    return "Hello from Python!"


# TODO (mom) make secure (API keys?)
@app.route("/add_user", methods = ['POST'])
def add_user():
    udata = json.loads(request.form['data']) # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    fbid = udata['id']
    print 'fbid = ' + fbid
    friends_raw = udata['friends']

    name = udata['name']
    names = name.split(" ")
    first_name = names[0]
    last_name = names[len(names) - 1]

    print 'name = ' + name

    # TODO (mom/rishi) add picture URL and load picture in background thread
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

    source = User.query.filter_by(fbid = sourceFbid).first() # TODO (mom) handle case when none is found
    reporter = User.query.filter_by(fbid = reporterFbid).first() # TODO (mom) same

    quote = Quote(source.id, reporter.id, content, location, False)

    db.session.add(quote)

    return 'quote added maybe? still need to commit'


#----------------------------------------
# launch
#----------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
