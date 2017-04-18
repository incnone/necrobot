def ordinal(num):
    suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
    if 10 <= num % 100 <= 20:
        suffix = 'th'
    else:
        suffix = suffixes.get(num % 10, 'th')
    return str(num) + suffix


def num_to_text(num):
    texts = {
        1: 'first',
        2: 'second',
        3: 'third',
        4: 'fourth',
        5: 'fifth',
        6: 'sixth',
        7: 'seventh',
        8: 'eighth',
        9: 'ninth',
        10: 'tenth',
        11: 'eleventh',
        12: 'twelfth',
        13: 'thirteenth',
        14: 'fourteenth',
        15: 'fifteenth',
        16: 'sixteenth',
        17: 'seventeenth',
        18: 'eighteenth',
        19: 'nineteenth',
        20: 'twentieth',
    }

    if num in texts:
        return texts[num]
    else:
        return ordinal(num)
