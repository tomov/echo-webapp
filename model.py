from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import select
from constants import DatabaseConstants
from sqlalchemy.orm import backref
from sqlalchemy import desc

db = SQLAlchemy()

# copied from http://stackoverflow.com/questions/9116924/how-can-i-achieve-a-self-referencing-many-to-many-relationship-on-the-sqlalchemy
friendship = db.Table(
    'friendships', 
    db.Column('friend_a_id', db.Integer, db.ForeignKey('users.id'), primary_key=True), 
    db.Column('friend_b_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    fbid = db.Column(db.String(length = 50), unique = True)
    email = db.Column(db.String(length = 50, collation = 'utf8_general_ci'), unique = True)
    first_name = db.Column(db.String(length = 50, collation = 'utf8_general_ci'))
    last_name = db.Column(db.String(length = 50, collation = 'utf8_general_ci'))
    picture_url = db.Column(db.Text)
    picture = db.Column(db.LargeBinary)
    registered = db.Column(db.Boolean)
    quotes_echoed = db.relationship('Echo', backref = 'users')
    comments = db.relationship('Comment', backref = 'user', lazy = 'dynamic')
    friends = db.relationship('User', secondary = friendship, primaryjoin=id==friendship.c.friend_a_id, secondaryjoin=id==friendship.c.friend_b_id)  # TODO (mom) make sure this works

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
    deleted = db.Column(db.Boolean)
    comments = db.relationship('Comment', backref = 'quote', lazy = 'dynamic')
    echoes = db.relationship('Echo', backref = 'quotes', lazy = 'dynamic')
    source = db.relationship('User', backref = 'quotes_sourced', foreign_keys = [source_id])
    reporter = db.relationship('User', backref = 'quotes_reported', foreign_keys = [reporter_id])

    def __init__(self, source_id, reporter_id, content = None, location = None, deleted = False):
        self.source_id = source_id
        self.reporter_id = reporter_id
        self.content = content
        self.location = location
        self.deleted = deleted
        self.created = datetime.utcnow()
        self.modified = self.created

    def __repr__(self):
        return '<Quote %r>' % self.content


# did this after http://docs.sqlalchemy.org/en/rel_0_7/orm/relationships.html, association object stuff
class Echo(db.Model):
    __tablename__ = 'echoes'
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'), primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key = True)
    def __init__(self, quote_id, user_id):
        self.quote_id = quote_id
        self.user_id = user_id
        self.created = datetime.utcnow()
        self.modified = self.created

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


# call this somewhere in application.py/home, run and open home page
# then check if db is created and then remove it
# TODO (mom) I know, it's super ghetto, but that's the easiest way for now
def create_db():
    db.create_all()
