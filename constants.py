class DatabaseConstants:
    DATABASE_URI_TEMPLATE = "mysql://ebroot:instaquote@aa1n9wwgoqy4mr8.cxexw98m36zh.us-east-1.rds.amazonaws.com/%s?init_command=set%%20character%%20set%%20utf8"
    DATABASE_NAME = 'echo_webapp'
    DATABASE_URI = DATABASE_URI_TEMPLATE % DATABASE_NAME

class DatetimeConstants:
    MYSQL_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class APIConstants:
    DEFAULT_GET_QUOTES_LIMIT = 30

class ErrorMessages:
    USER_IS_ALREADY_REGISTERED = "User has already registered"
    USER_NOT_REGISTERED = "User has been added by a friend but is not yet registered"
    SOURCE_NOT_FOUND = "Source with given fbid does not exist"
    REPORTER_NOT_FOUND = "Reporter with given fbid does not exist"
    USER_NOT_FOUND = "User with given fbid does not exist"
    USERS_NOT_FRIENDS = "Users are not friends"
    QUOTE_NOT_FOUND = "Quote with given id does not exist"

class SuccessMessages:
    USER_ADDED = "User was added successfully!"
    FRIENDSHIP_DELETED = "Users were unfriended successfully!"
    QUOTE_ADDED = "Quote was added successfully!"
    QUOTE_DELETED = "Quote was deleted successfully!"
    COMMENT_ADDED = "Comment was added successfully!"
    USER_UPDATED = "User was updated successfully!"
    ECHO_ADDED = "Quote was echoed successfully!"
    ECHO_DELETED = "Quote was unechoed successfully!"
