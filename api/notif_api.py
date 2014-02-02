# -*- coding: utf-8 -*-

from api_imports import *
from sqlalchemy import desc
from apns import APNs, Payload
from model import Echo, Notification, NotifPrefs

notif_api = Blueprint('notif_api', __name__)

# note that we don't db.session.commit -- the caller must do that after
def add_notification(user, quote, type, recipient_id):

    #print 'ADD NOTIFICATION from user ' + str(user.id) + ' quote ' + str(quote.id) + ' type ' + str(type) + ' for recipient ' + str(recipient_id)
    # add notification to db
    recipient = User.query.filter_by(id=recipient_id).first()
    if not recipient:
        return
    if recipient not in user.all_friends:
        return
    if not recipient.registered:
        return
    ids = [friend.id for friend in recipient.all_friends] + [recipient.id]
    echo = Echo.query.filter(Echo.quote == quote, Echo.user_id.in_(ids)).order_by(Echo.id).first()

    notification = Notification(user, quote, echo, type)
    notification.recipients.append(recipient)
    db.session.add(notification)

    # send push notification to device
    formatted_text = notification_to_text(notification)
    token_hex = recipient.device_token
#    test_notif('token is' + str(token_hex)) # MOM remove
    if not token_hex:
        return
    #print 'send text ' + formatted_text['text']
    try:
        send_notification(token_hex, formatted_text['text'])
    except Exception as e:
        #raise  # TODO FIXME this is for debugging purposes only -- remove after testing!
        return

# MOM remove
@notif_api.route("/test_notif", methods = ['get'])
def test_notif(string):
    formatted_text = dict()
    formatted_text['text'] = string
    token_hex = "a951d8aba5ec3532edc6426583681e3749e2b71c9e1724219897382efd8154b0"
    #print 'send text ' + formatted_text['text']
    send_notification(token_hex, formatted_text['text'])
    return
   

def notification_to_text(notification):
    user = notification.user
    quote = notification.quote
    content = quote.content.encode('utf8')
    first_name = user.first_name.encode('utf8')
    last_name = user.last_name.encode('utf8')
    if content[-1:].isalpha() or content[-1:].isdigit():
        content += '.'
    if notification.type == 'quote':
        return {
            'text': "{0} {1} posted a quote by you!".format(first_name, last_name),
            'bold': [{
                    'location': 0,
                    'length': len(first_name) + len(last_name) + 1
                }]
        }
    elif notification.type == 'echo':
        return {
            'text': "{0} {1} echoed your quote: \"{2}\"".format(first_name, last_name, content),
            'bold': [{
                    'location': 0,
                    'length': len(first_name) + len(last_name) + 1
                }]
        }
    elif notification.type == 'comment':
        return {
            'text': "{0} {1} commented on your quote.".format(first_name, last_name, quote.content),
            'bold': [{
                    'location': 0,
                    'length': len(first_name) + len(last_name) + 1
                }]
        }
    elif notification.type == 'fav':
        return {
            'text': "{0} {1} favorited your quote: \"{2}\"".format(first_name, last_name, content),
            'bold': [{
                    'location': 0,
                    'length': len(first_name) + len(last_name) + 1
                }]
        }
    else:
        return None

def notification_dict_from_obj(notification):
    notification_res = dict()
    notification_res['_id'] = str(notification.quote_id)
    notification_res['order_id'] = str(notification.echo_id)
    notification_res['type'] = notification.type
    notification_res['unread'] = notification.unread
    notification_res['timestamp'] = datetime_to_timestamp(notification.created) # doesn't jsonify
    notification_res['formatted-text'] = notification_to_text(notification)
    return notification_res

@notif_api.route("/get_notifications", methods = ['get'])
@authenticate
@track
def get_notifications(user_id):
    unread_only = request.args.get('unread_only')
    limit = request.args.get('limit')
    clear = request.args.get('clear')

    try:
        user = User.query.filter(User.id == user_id).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        if not limit:
            if unread_only != '1':
                notifications = Notification.query.filter(Notification.recipients.any(User.id == user.id)).order_by(desc(Notification.id)).all()
            else:
                notifications = Notification.query.filter(Notification.recipients.any(User.id == user.id), Notification.unread).order_by(desc(Notification.id)).all()
        else:
            if unread_only != '1':
                notifications = Notification.query.filter(Notification.recipients.any(User.id == user.id)).order_by(desc(Notification.id)).limit(limit).all()
            else:
                notifications = Notification.query.filter(Notification.recipients.any(User.id == user.id), Notification.unread).order_by(desc(Notification.id)).limit(limit).all()

        result = []
        for notification in notifications:
            notification_res = notification_dict_from_obj(notification)
            result.append(notification_res)
            if clear == '1':
                notification.unread = False

        db.session.commit() # update unreads

        return format_response(result)
    except ServerException as e:
        return format_response(None, e)


@notif_api.route("/get_notifprefs", methods = ['get'])
@authenticate
@track
def get_notifprefs(user_id):
    try:
        user = User.query.filter(User.id == user_id).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        if not user.notifprefs:
            user.notifprefs = NotifPrefs()
            db.session.commit()

        notifprefs = {
            'quotes': user.notifprefs.quotes,
            'echoes': user.notifprefs.echoes,
            'comments': user.notifprefs.comments,
            'favs': user.notifprefs.favs
        }

        return format_response(notifprefs)
    except ServerException as e:
        return format_response(None, e)


@notif_api.route("/set_notifprefs", methods = ['post'])
@authenticate
@track
def set_notifprefs(user_id):
    data = json.loads(request.values.get('data'))
    quotes = data.get('quotes')
    echoes = data.get('echoes')
    comments = data.get('comments')
    favs = data.get('favs')

    try:
        user = User.query.filter(User.id == user_id).first()
        if not user:
            raise ServerException(ErrorMessages.USER_NOT_FOUND, \
                ServerException.ER_BAD_USER)

        if not user.notifprefs:
            user.notifprefs = NotifPrefs()
            db.session.commit()

        if quotes is not None:
            user.notifprefs.quotes = quotes
        if echoes is not None:
            user.notifprefs.echoes = echoes
        if comments is not None:
            user.notifprefs.comments = comments
        if favs is not None:
            user.notifprefs.favs = favs
        db.session.commit()

        return format_response(SuccessMessages.NOTIFPREFS_SET)
    except ServerException as e:
        return format_response(None, e)


def send_notification(token_hex, text):
    apns = APNs(use_sandbox=False, cert_file='certificates/EchoAPNSProdCert.pem', key_file='certificates/newEchoAPNSProdKey.pem')
    payload = Payload(alert=text, sound="default", badge=0)
    apns.gateway_server.send_notification(token_hex, payload)

