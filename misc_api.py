# -*- coding: utf-8 -*-

import json
from flask import request, Blueprint

from model import db, User, Feedback
from auth import *
from util import *
from auth import *
from constants import *

misc_api = Blueprint('misc_api', __name__)

# TODO this is just for Apple
@misc_api.route('/add_feedback_from_support', methods = ['POST'])
def add_feedback_from_support():
    name = request.form['name']
    email = request.form['email']
    text = request.form['text']

    content = json.dumps({'name': name, 'email': email, 'text': text});
    feedback = Feedback(6416, content)
    db.session.add(feedback)
    db.session.commit()
    return '<p style="align: center">Thank you for your feedback! We will review it and get back to you as soon as possible.</p>'


@misc_api.route('/add_feedback', methods = ['POST'])
@authenticate
@track
def add_feedback(user_id):
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



@misc_api.route('/og_repeater', methods=['get'])
def open_graph_repeater():
    return render_template('og.html', tags=request.args, url=request.url)

@misc_api.route('/og_quote', methods=['get'])
def og_quote():
    echoId = request.args.get('ref')

    try:
        echo = Echo.query.filter_by(id = echoId).first()
        if not echo:
            raise ServerException(ErrorMessages.ECHO_NOT_FOUND, \
                ServerException.ER_BAD_ECHO)
        quote = echo.quote
        if not quote or quote.deleted:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        # TODO there is some code duplication with get_quotes below... we should think if it could be avoided
        is_echo = echo.user_id != quote.reporter_id
        if is_echo:
            quote.created = echo.created
            quote.reporter = echo.user

        tags = {
            'og:type': 'echoios:quote',
            'og:title': '"%s"' % quote.content,
            'og:image': 'http://graph.facebook.com/%s/picture?width=200' % quote.source.fbid,
            'og:description': u'\u2014 %s %s' % (quote.source.first_name, quote.source.last_name)
        }
        return render_template('og.html', tags=tags, url=request.url) 
    except ServerException as e:
        return format_response(None, e)
