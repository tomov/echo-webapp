from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime)
    fbid = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(50), unique=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    picture_url = db.Column(db.Text)
    picture = db.Column(db.LargeBinary)
    registered = db.Column(db.Boolean)

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
