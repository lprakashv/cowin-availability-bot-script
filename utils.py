def escape(text):
    for c in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        if c in text:
            text = text.replace(c, str('\\' + c))
    return text


def bold(text):
    if type(text) == list:
        return [bold(t) for t in text]
    elif type(text) == str:
        return '*' + text + "*"
    else:
        text


def underline(text):
    if type(text) == list:
        return [underline(t) for t in text]
    elif type(text) == str:
        return '__' + text + "__"
    else:
        text
