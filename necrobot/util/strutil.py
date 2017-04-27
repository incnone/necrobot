def escaped(s):
    for char in ['*', '-', '_']:
        s = s.replace(char, '\\' + char)
    return s
