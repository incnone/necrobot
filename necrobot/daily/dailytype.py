from enum import Enum


# Remark: The value of this enum is used for storing results in the database, and so
# old values should never be changed or reused.
class DailyType(Enum):
    cadence = 0
    rotating = 1

rotating_daily_chars = ['Eli', 'Bolt', 'Dove', 'Aria', 'Bard', 'Dorian', 'Coda', 'Melody', 'Monk']


def character(daily_type, daily_number):
    if daily_type == DailyType.cadence:
        return 'Cadence'
    elif daily_type == DailyType.rotating:
        return rotating_daily_chars[daily_number % 9]


def leaderboard_header(daily_type, daily_number):
    if daily_type == DailyType.cadence:
        return 'Cadence Speedrun Daily'
    elif daily_type == DailyType.rotating:
        return 'Rotating Speedrun Daily ({0})'.format(character(daily_type, daily_number))


def days_until(charname, daily_number):
    days = 0
    today_char = character(DailyType.rotating, daily_number)

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


def parse_out_type(command_args, daily_number):
    arg_to_cull = None
    parsed_args = []
    for i, arg in enumerate(command_args):
        parg = _parse_dailytype_arg(arg, daily_number)
        if parg:
            arg_to_cull = i
            parsed_args.append(parg)

    if not parsed_args:
        return DailyType.cadence
    elif len(parsed_args) == 1:
        del command_args[arg_to_cull]
        parg = parsed_args[0]
        if parg == 'cadence':
            return DailyType.cadence
        elif parg == 'rotating':
            return DailyType.rotating
    else:
        return None


def _parse_dailytype_arg(arg, daily_number):
    sarg = arg.lstrip('-').lower()
    if sarg == 'cadence':
        return 'cadence'
    elif sarg == 'rot' or sarg == 'rotating' or sarg == character(DailyType.rotating, daily_number).lower():
        return 'rotating'
    else:
        return None
