from enum import Enum


# Remark: The value of this enum is used for storing results in the database, and so
# old values should never be changed or reused.
class DailyType(Enum):
    CADENCE = 0
    ROTATING = 1

    def __str__(self):
        if self == DailyType.CADENCE:
            return 'Cadence'
        elif self == DailyType.ROTATING:
            return 'rotating-character'


rotating_daily_chars = [
    'Eli',
    'Diamond',
    'Bolt',
    'Dove',
    'Aria',
    'Bard',
    'Dorian',
    'Coda',
    'Nocturna',
    'Melody',
    'Monk']


def character(daily_type, daily_number):
    if daily_type == DailyType.CADENCE:
        return 'Cadence'
    elif daily_type == DailyType.ROTATING:
        return rotating_daily_chars[daily_number % len(rotating_daily_chars)]


def leaderboard_header(daily_type, daily_number):
    if daily_type == DailyType.CADENCE:
        return 'Cadence Speedrun Daily'
    elif daily_type == DailyType.ROTATING:
        return 'Rotating Speedrun Daily ({0})'.format(character(daily_type, daily_number))


def days_until(charname, daily_number):
    days = 0
    today_char = character(DailyType.ROTATING, daily_number)

    found_start = False
    for char in rotating_daily_chars:
        if char == today_char:
            found_start = True
        elif found_start:
            days += 1
            if char == charname:
                return days

    for char in rotating_daily_chars:
        days += 1
        if char == charname:
            return days


def parse_out_type(command_args: list):
    arg_to_cull = None
    parsed_args = []
    for i, arg in enumerate(command_args):
        parg = _parse_dailytype_arg(arg)
        if parg:
            arg_to_cull = i
            parsed_args.append(parg)

    if not parsed_args:
        return DailyType.CADENCE
    elif len(parsed_args) == 1:
        command_args.pop(arg_to_cull)
        parg = parsed_args[0]
        if parg == 'cadence':
            return DailyType.CADENCE
        elif parg == 'rotating':
            return DailyType.ROTATING
    else:
        return None


def _parse_dailytype_arg(arg):
    sarg = arg.lstrip('-').lower()
    if sarg == 'cadence':
        return 'cadence'
    elif sarg == 'rot' or sarg == 'rotating':
        return 'rotating'
    else:
        return None
