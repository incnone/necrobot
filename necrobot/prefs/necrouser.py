import pytz

from necrobot.botbase.necrodb import NecroDB
from .userprefs import UserPrefs
from ..util import strutil


class DuplicateUserException(Exception):
    def __init__(self, err_str):
        self._err_str = err_str

    def __str__(self):
        return self._err_str


class NecroUser(object):
    @staticmethod
    def get_user(discord_id=None, discord_name=None, twitch_name=None, rtmp_name=None):
        if discord_id is None and discord_name is None and twitch_name is None and rtmp_name is None:
            raise RuntimeError('Error: Called NecroUser.get_user with no non-None fields.')

        raw_db_data = NecroDB().get_all_users(discord_id, discord_name, twitch_name, rtmp_name)
        if not raw_db_data:
            return None
        elif len(raw_db_data) > 1:
            raise DuplicateUserException(
                'Two or more users found satisfying discord_id={0}, discord_name={1}, twitch_name={2}, '
                'rtmp_name={3}.'.format(discord_id, discord_name, twitch_name, rtmp_name))

        for row in raw_db_data:
            user = NecroUser()
            user.discord_id = int(row[0])
            user.discord_name = row[1]
            user.twitch_name = row[2]
            user.rtmp_name = row[3]
            user.timezone = pytz.timezone(row[4]) if row[4] is not None else None
            user.user_info = row[5]
            user.user_prefs = UserPrefs()
            user.user_prefs.daily_alert = bool(row[6])
            user.user_prefs.race_alert = bool(row[7])
            return user

    def __init__(self):
        self.discord_id = None
        self.discord_name = None
        self.twitch_name = None
        self.rtmp_name = None
        self.timezone = None
        self.user_info = None
        self.user_prefs = None

    def __eq__(self, other):
        return self.discord_id == other.discord_id

    @property
    def infoname(self):
        if self.user_info is not None:
            return '{0} ({1})'.format(self.discord_name, self.user_info)
        else:
            return self.discord_name

    @property
    def infotext(self):
        if self.twitch_name == self.rtmp_name:
            return '  Twitch/RTMP: {0}\n' \
                   '     Timezone: {1}'.format(
                    self.rtmp_name,
                    self.timezone)
        else:
            return '    Twitch: {0}\n' \
                   '      RTMP: {1}\n' \
                   '  Timezone: {2}'.format(
                    self.twitch_name,
                    self.rtmp_name,
                    self.timezone)

    @property
    def infobox(self):
        return '```\n' \
               '{0}\n' \
               '{1}```'.format(
                    self.infoname,
                    self.infotext)

    @property
    def escaped_twitch_name(self):
        return strutil.escaped(self.twitch_name)

    @property
    def escaped_rtmp_name(self):
        return strutil.escaped(self.rtmp_name)

    def utc_to_local(self, utc_dt):
        if self.timezone not in pytz.all_timezones:
            return None
        local_tz = pytz.timezone(self.timezone)

        if utc_dt.tzinfo is not None and utc_dt.tzinfo.utcoffset(utc_dt) is not None:
            return local_tz.normalize(utc_dt.astimezone(local_tz))
        else:
            return local_tz.normalize(pytz.utc.localize(utc_dt))

    def local_to_utc(self, local_dt):
        if self.timezone not in pytz.all_timezones:
            return None
        local_tz = pytz.timezone(self.timezone)

        if local_dt.tzinfo is not None and local_dt.tzinfo.utcoffset(local_dt) is not None:
            return pytz.utc.normalize(local_dt.astimezone(pytz.utc))
        else:
            return pytz.utc.normalize(local_tz.localize(local_dt))