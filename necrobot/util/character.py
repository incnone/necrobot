from enum import Enum


class NDChar(Enum):
    Cadence = 0
    Melody = 1
    Aria = 2
    Dorian = 3
    Eli = 4
    Monk = 5
    Dove = 6
    Coda = 7
    Bolt = 8
    Bard = 9
    Story = 10
    All = 11
    Nocturna = 12
    Diamond = 13

    @staticmethod
    def fromstr(char_name):
        for ndchar in NDChar:
            if ndchar.name == char_name.capitalize():
                return ndchar

    def __str__(self):
        return self.name

    @property
    def levels_reversed(self):
        return self == NDChar.Aria


def get_char_from_str(char_name):
    for ndchar in NDChar:
        if ndchar.name == char_name.capitalize():
            return ndchar


def get_str_from_char(char):
    if char is not None:
        return char.name
    else:
        return ''
