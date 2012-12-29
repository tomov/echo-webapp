from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import select

db = SQLAlchemy()


# copied from http://stackoverflow.com/questions/9116924/how-can-i-achieve-a-self-referencing-many-to-many-relationship-on-the-sqlalchemy
friendship = db.Table(
    'friendship', 
    db.Column('friend_a_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_b_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)          

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    fbid = db.Column(db.String(50), unique = True)
    email = db.Column(db.String(50), unique = True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    picture_url = db.Column(db.Text)
    picture = db.Column(db.LargeBinary)
    registered = db.Column(db.Boolean)
    quotes = db.relationship('Quote', backref = 'user', lazy = 'dynamic') # TODO (mom) how the fuck is this supposed to work?
    quotes_echoed = db.relationship('Echo', backref = 'user')
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
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    source_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    location = db.Column(db.String(50))
    deleted = db.Column(db.Boolean)
    comments = db.relationship('Comment', backref = 'quote', lazy = 'dynamic')
    echoes = db.relationship('Echo', backref = 'quote', lazy = 'dynamic')

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
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key = True)
    quote = db.relationship('Quote', backref = 'user_assoc')
    def __init__(self, quote_id, user_id):
        self.quote_id = quote_id
        self.user_id = user_id
        self.created = datetime.utcnow()
        self.modified = self.created

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'))
    content = db.Column(db.Text)

    def __init__(self, user_id, quote_id, content = None):
        self.user_id = user_id
        self.quote_id = quote_id
        self.content = content
        self.created = datetime.utcnow()
        self.modified = self.created

    def __repr__(self):
        return '<Comment %r>' % self.content


