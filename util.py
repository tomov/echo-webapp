import time
import json

def split_name(name):
    names = name.encode('utf-8').split(" ")
    if len(names) == 0:
        return "", ""
    if len(names) == 1:
        return names[0], ""
    return names[0], names[len(names) - 1]

def datetime_to_timestamp(date):
    return time.mktime(date.timetuple())


def format_response(ret=None, error=None):
    if ret is None:
        ret = {}
    elif isinstance(ret, basestring):
        ret = {'message' : ret}
    if error:
        #assert isinstance(error, ServerException)
        ret['error'] = error.to_dict() 
    return json.dumps(ret)

