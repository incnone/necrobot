def escaped(s):
    for char in ['*', '-', '_']:
        s = s.replace(char, '\\' + char)
    return s


def tickless(s):
    return s.replace('```', '`\u200b`\u200b`\u200b')
