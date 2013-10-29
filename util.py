import time
import json
import collections

def split_name(name):
    names = name.encode('utf-8').split(" ")
    if len(names) == 0:
        return "", ""
    if len(names) == 1:
        return names[0], ""
    return names[0], " ".join(names[1:])

def datetime_to_timestamp(date):
    return time.mktime(date.timetuple())

def dict_to_unicode_dict(data):
    if isinstance(data, basestring):
        return data.decode('utf8')
    elif isinstance(data, collections.Mapping):
        return dict(map(dict_to_unicode_dict, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(dict_to_unicode_dict, data))
    else:
        return data
