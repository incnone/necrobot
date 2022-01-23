import calendar
import datetime
import pytz


def timedelta_to_str(td, punctuate=False):
    if punctuate and td < datetime.timedelta(minutes=1):
        return 'Right now! :runner: :checkered_flag:'

    hrs = int(td.seconds // 3600)
    mins = int((td.seconds - hrs * 3600) // 60)

    output_str = ''
    if td.days > 0:
        output_str += '{0} day{1}, '.format(td.days, '' if td.days == 1 else 's')
    if hrs > 0:
        output_str += '{0} hour{1}, '.format(hrs, '' if hrs == 1 else 's')
    if mins > 0:
        output_str += '{0} minute{1}, '.format(mins, '' if mins == 1 else 's')

    if punctuate:
        return output_str[:-2] + '.'
    else:
        return output_str[:-2]


def discord_timestamp_for_match(dt: datetime.datetime) -> str:
    suppress_date_delta = datetime.timedelta(hours=18)

    delta = dt - pytz.utc.localize(datetime.datetime.utcnow())
    timestamp = int(dt.timestamp())
    if delta < datetime.timedelta(seconds=0):
        return f'Right now! :runner: :checkered_flag: (Started <t:{timestamp}:R>)'
    elif delta < suppress_date_delta:
        return f'<t:{timestamp}:t> (<t:{timestamp}:R>)'
    else:
        return f'<t:{timestamp}:F>'


def str_full_12h(dt):
    if not dt:
        return ''

    weekday = calendar.day_name[dt.weekday()]
    day = dt.strftime("%d").lstrip('0')
    hour = dt.strftime("%I").lstrip('0')
    pm_str = dt.strftime("%p").lower()
    datestr = dt.strftime("%b {0} @ {1}:%M{2} %Z".format(day, hour, pm_str))
    return weekday + ', ' + datestr


def str_full_24h(dt):
    if not dt:
        return ''

    weekday = calendar.day_name[dt.weekday()]
    day = dt.strftime("%d").lstrip('0')
    hour = dt.strftime("%H").lstrip('0')
    if hour == '':
        hour = '00'
    datestr = dt.strftime("%b {0} @ {1}:%M %Z".format(day, hour))
    return weekday + ', ' + datestr


def str_dateonly(dt):
    weekday = calendar.day_name[dt.weekday()]
    day = dt.strftime("%d").lstrip('0')
    return dt.strftime("{0}, %b {1}".format(weekday, day))


def str_timeonly(dt):
    hour = dt.strftime("%I").lstrip('0')
    pm_str = dt.strftime("%p").lower()
    return dt.strftime("{0}:%M{1}".format(hour, pm_str))
