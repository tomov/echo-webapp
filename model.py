from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import select
from constants import DatabaseConstants
from sqlalchemy.orm import backref
from sqlalchemy import desc
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import UniqueConstraint


db = SQLAlchemy()

# copied from http://stackoverflow.com/questions/9116924/how-can-i-achieve-a-self-referencing-many-to-many-relationship-on-the-sqlalchemy
friendship = db.Table(
    'friendships', 
    db.Column('friend_a_id', db.Integer, db.ForeignKey('users.id'), primary_key=True), 
    db.Column('friend_b_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

notifications_recipients = db.Table(
    'notifications_recipients', 
    db.Column('notification_id', db.Integer, db.ForeignKey('notifications.id')), 
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'))
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    fbid = db.Column(db.String(length = 50), primary_key = True)
    email = db.Column(db.String(length = 50, collation = 'utf8_general_ci'), unique = True)
    first_name = db.Column(db.String(length = 50, collation = 'utf8_general_ci'))
    last_name = db.Column(db.String(length = 50, collation = 'utf8_general_ci'))
    picture_url = db.Column(db.Text)
    picture = db.Column(db.LargeBinary)
    registered = db.Column(db.Boolean)
    notifprefs_id = db.Column(db.Integer, db.ForeignKey('notifprefs.id'))
    notifprefs = db.relationship("NotifPrefs", backref="user")
    echoes = association_proxy('users_echoes', 'quote')
    comments = db.relationship('Comment', backref = 'user', lazy = 'dynamic')
    feedback = db.relationship('Feedback', backref = 'user', lazy = 'dynamic')
    friends = db.relationship('User', secondary = friendship, primaryjoin=id==friendship.c.friend_a_id, secondaryjoin=id==friendship.c.friend_b_id)  # TODO (mom) make sure this works
    device_token = db.Column(db.String(length = 64))

    def __init__(self, fbid, email = None, first_name = None, last_name = None, picture_url = None, picture = None, registered = False):
        self.fbid = fbid
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.picture_url = picture_url
        self.registered = registered
        self.created = datetime.utcnow()
        self.modified = self.created

    def __repr__(self):
        return '<User %r %r>' % (self.first_name, self.last_name)


# this relationship is viewonly and selects across the union of all
# friends
# again, taken from http://stackoverflow.com/questions/9116924/how-can-i-achieve-a-self-referencing-many-to-many-relationship-on-the-sqlalchemy
friendship_union = select([
                        friendship.c.friend_a_id, 
                        friendship.c.friend_b_id
                        ]).union(
                            select([
                                friendship.c.friend_b_id, 
                                friendship.c.friend_a_id]
                            )
                    ).alias()
User.all_friends = db.relationship('User',
                       secondary=friendship_union,
                       primaryjoin=User.id==friendship_union.c.friend_a_id,
                       secondaryjoin=User.id==friendship_union.c.friend_b_id,
                       viewonly=True) 


class Quote(db.Model):
    __tablename__ = 'quotes'
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    source_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.Text)
    location = db.Column(db.String(length = 50, collation = 'utf8_general_ci'))
    location_lat = db.Column(db.Float(precision = 32))   # Note: this is in an alembic revison 
    location_long = db.Column(db.Float(precision = 32))  # Note: alembic
    deleted = db.Column(db.Boolean)
    echoers = association_proxy('quotes_echoes', 'user');
    comments = db.relationship('Comment', backref = 'quote', lazy = 'dynamic')
    source = db.relationship('User', backref = 'quotes_sourced', foreign_keys = [source_id])
    reporter = db.relationship('User', backref = 'quotes_reported', foreign_keys = [reporter_id])

    def __init__(self, source_id, reporter_id, content = None, location = None, location_lat = None, location_long = None, deleted = False):
        self.source_id = source_id
        self.reporter_id = reporter_id
        self.content = content
        self.location = location
        self.location_lat = location_lat
        self.location_long = location_long
        self.deleted = deleted
        self.created = datetime.utcnow()
        self.modified = self.created

    def __repr__(self):
        return '<Quote %r>' % self.content

class Echo(db.Model):
    __tablename__ = 'echoes'
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'), primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key = True)
    quote = db.relationship("Quote",
        backref = backref("quotes_echoes", cascade="all, delete-orphan"))
    user = db.relationship("User", backref = "users_echoes") 
    __table_args__ = (UniqueConstraint('quote_id', 'user_id', name='unique-echoer-quote-pair'), )

    def __init__(self, user):
        self.user = user
        self.created = datetime.utcnow()
        self.modified = self.created

    def __repr__(self):
        return '<Echo [Quote %r] [User %r]>' % (self.quote.id, self.user.id)

class Favorite(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'), primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key = True)
    quote = db.relationship("Quote", backref="favs")
    user = db.relationship("User", backref="favs")
    __table_args__ = (UniqueConstraint('quote_id', 'user_id', name='unique-favorite'), )
    def __init__(self, quote):
        self.quote = quote
        self.created = datetime.utcnow()
        self.modified = self.created

    def __repr__(self):
        return '<Favorite [Quote %r] [User %r]>' % (self.quote.id, self.user.id)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'))
    content = db.Column(db.Text)

    def __init__(self, user_id, quote_id, content = None):
        self.user_id = user_id
        self.quote_id = quote_id
        self.content = content
        self.created = datetime.utcnow()
        self.modified = self.created

    def __repr__(self):
        return '<Comment %r>' % self.content

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.Text)
    version = db.Column(db.String(length = 30))

    def __init__(self, user_id, content = None, version = None):
        self.user_id = user_id
        self.content = content
        self.version = version
        self.created = datetime.utcnow()
        self.modified = self.created

    def __repr__(self):
        return '<Feedback %r>' % self.content

# for auth
class Access_Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True)
    access_token = db.Column(db.Text)

    def __init__(self, userid, token=None):
        self.user_id = userid
        self.access_token = token

    def __repr__(self):
        return '[id: {2}; user_id: {0}; access_token: {1}]'.format(self.user_id, self.access_token, self.id)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    type = db.Column(db.Enum('quote', 'echo', 'comment', 'fav'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'))
    echo_id = db.Column(db.Integer, db.ForeignKey('echoes.id'))
    unread = db.Column(db.Boolean)
    quote = db.relationship("Quote", backref="notifications")
    echo = db.relationship("Echo", backref="notifications")
    user = db.relationship("User", backref="notifications_authored")
    recipients = db.relationship("User", secondary = notifications_recipients, backref="notifications_received")

    def __init__(self, user, quote, echo, type=None):
        self.user = user
        self.quote = quote
        self.echo = echo
        self.type = type
        self.unread = True
        self.created = datetime.utcnow()
        self.modified = self.created

    def __repr__(self):
        return '<Notification %r>' % self.type

class NotifPrefs(db.Model):
    __tablename__ = 'notifprefs'
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    quotes = db.Column(db.Boolean)
    echoes = db.Column(db.Boolean)
    comments = db.Column(db.Boolean)
    favs = db.Column(db.Boolean)

    def __init__(self):
        self.quotes = True
        self.echoes = True
        self.comments = True
        self.favs = True
        self.created = datetime.utcnow()
        self.modified = self.created

    def __repr__(self):
        return '<NotifPrefs %r>' % self.user_id

# call this somewhere in application.py/home, run and open home page
# then check if db is created and then remove it
# TODO (mom) I know, it's super ghetto, but that's the easiest way for now
def create_db():
    db.create_all()
