import re


def escaped(s):
    for char in ['*', '-', '_']:
        s = s.replace(char, '\\' + char)
    return s


def regex(s):
    return re.compile(r'(?i)^\s*' + re.escape(s) + r'\s*$')
