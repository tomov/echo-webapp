# -*- coding: utf-8 -*-

import json
from flask import request

from application import app
from model import db, Feedback

# TODO this is just for Apple
@app.route('/add_feedback_from_support', methods = ['POST'])
def add_feedback_from_support():
    name = request.form['name']
    email = request.form['email']
    text = request.form['text']

    content = json.dumps({'name': name, 'email': email, 'text': text});
    feedback = Feedback(6416, content)
    db.session.add(feedback)
    db.session.commit()
    return '<p style="align: center">Thank you for your feedback! We will review it and get back to you as soon as possible.</p>'


@app.route('/add_feedback', methods = ['POST'])
def add_feedback():

    # !AUTH -- TODO: put in method -- decorator
    #----------------------------------
    token = request.args.get('token')
    try:
        user_id = authorize_user(token)
    except AuthException as e:
        return format_response(None, e)
    track_event(user_id, "add_feedback")
    #-----------------------------------

    data = json.loads(request.values.get('data'))
    content = data['content']
    version = data['version']
   
    try:
        user = User.query.filter_by(id = user_id).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        feedback = Feedback(user_id, content, version)
        db.session.add(feedback)
        db.session.commit()
        return format_response(SuccessMessages.FEEDBACK_ADDED)
    except ServerException as e:
        return format_response(None, e)


