def split_name(name):
    names = name.encode('utf-8').split(" ")
    if len(names) == 0:
        return "", ""
    if len(names) == 1:
        return names[0], ""
    return names[0], names[len(names) - 1]



