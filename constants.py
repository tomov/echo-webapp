class DatabaseConstants:
    DATABASE_URI_TEMPLATE = "mysql://ebroot:instaquote@aa1n9wwgoqy4mr8.cxexw98m36zh.us-east-1.rds.amazonaws.com/%s?charset=utf8&init_command=set%%20character%%20set%%20utf8"
    DATABASE_LOCAL_URI_TEMPLATE = "mysql://root:mainatati@127.0.0.1/%s?charset=utf8&init_command=set%%20character%%20set%%20utf8"
    DATABASE_NAME = 'echo_webapp'
    DATABASE_URI = DATABASE_URI_TEMPLATE % DATABASE_NAME

class DatetimeConstants:
    MYSQL_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class APIConstants:
    DEFAULT_GET_QUOTES_LIMIT = 30

# you take these from here: https://developers.facebook.com/apps/193862260739040/summary
# and the token you get from here (replace ID and SECRET accordingly): https://graph.facebook.com/oauth/access_token?%20client_id=193862260739040&client_secret=c1738548c8dd39f385d778d2d4baa296&grant_type=client_credentials
class FacebookConstants:
    APP_ID = '193862260739040'
    APP_SECRET = 'c1738548c8dd39f385d778d2d4baa296'
    APP_TOKEN = "193862260739040|KCleMZh3OwN2tm4xrdr69yT91Ws"
    GET_TEST_USERS_URI = "https://graph.facebook.com/%s/accounts/test-users?access_token=%s" % (APP_ID, APP_TOKEN)

class ErrorMessages:
    USER_IS_ALREADY_REGISTERED = "User has already registered"
    USER_NOT_REGISTERED = "User has been added by a friend but is not yet registered"
    SOURCE_NOT_FOUND = "Source with given fbid does not exist"
    REPORTER_NOT_FOUND = "Reporter with given fbid does not exist"
    SAME_SOURCE_REPORTER = "Reporter and source must be different"
    USER_NOT_FOUND = "User with given fbid does not exist"
    USERS_NOT_FRIENDS = "Users are not friends"
    QUOTE_NOT_FOUND = "Quote with given id does not exist"
    COMMENT_NOT_FOUND = "Comment with given id does not exist"
    FAV_ALREADY_EXISTS = "User has already favorited this quote"
    ECHO_ALREADY_EXISTS = "User has already echoed this quote"
    ECHO_EXISTENTIAL_CRISIS = "This echo does not exist"
    FAV_EXISTENTIAL_CRISIS = "This favorite doesn't exist"
    ECHO_NOT_FOUND = "Echo does not exist"
    DEVICE_TOKEN_EXISTS = "This device token is already registered for some other user"

class SuccessMessages:
    FRIENDSHIP_ADDED = "Users friended successfully!";
    USER_ADDED = "User was added successfully!"
    FRIENDSHIP_DELETED = "Users were unfriended successfully!"
    QUOTE_ADDED = "Quote was added successfully!"
    QUOTE_DELETED = "Quote was deleted successfully!"
    COMMENT_ADDED = "Comment was added successfully!"
    COMMENT_DELETED = "Comment was deleted successfully!"
    USER_UPDATED = "User was updated successfully!"
    ECHO_ADDED = "Quote was echoed successfully!"
    ECHO_DELETED = "Quote was unechoed successfully!"
    FAV_ADDED = "Favorite was added successfully!"
    FAV_DELETED = "Favorite was deleted successfully!"
    FEEDBACK_ADDED = "Feedback was added successfully!"
    TOKEN_REGISTERED = "Device token was registered successfully!"
    NOTIFPREFS_SET = "Notification preferences set successfully!"
    USER_LOGGED_OUT = "User logged out successfully!"
    GREAT_SUCCESS = "It's a great success!!"