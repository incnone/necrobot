import datetime
import pytz

from dateutil import parser
from necrobot.util.parse.exception import ParseException


class CustomParserInfo(parser.parserinfo):
    WEEKDAYS = [
        ('Mon', 'Monday'),
        ('Tue', 'Tues', 'Tuesday'),
        ('Wed', 'Wednesday'),
        ('Thu', 'Thurs', 'Thursday'),
        ('Fri', 'Friday'),
        ('Sat', 'Saturday'),
        ('Sun', 'Sunday')
    ]


def parse_datetime(parse_str: str, timezone: pytz.timezone = pytz.utc) -> datetime.datetime:
    if parse_str.lower() == 'now':
        return pytz.utc.localize(datetime.datetime.utcnow())

    try:
        dateutil_parse = parser.parse(
            parse_str,
            fuzzy=True,
            dayfirst=False,
            yearfirst=False)
        if 'tomorrow' in parse_str:
            return timezone.localize(dateutil_parse + datetime.timedelta(days=1)).astimezone(pytz.utc)
        else:
            return timezone.localize(dateutil_parse).astimezone(pytz.utc)
    except ValueError:
        raise ParseException('Couldn\'t parse {0} as a time.'.format(parse_str))
