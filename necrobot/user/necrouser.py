import pytz

from necrobot.botbase import necrodb
from necrobot.user.userprefs import UserPrefs
from necrobot.util import strutil
from necrobot.util import console


class DuplicateUserException(Exception):
    def __init__(self, err_str):
        self._err_str = err_str

    def __str__(self):
        return self._err_str


class NecroUser(object):
    @staticmethod
    def get_user(necrobot, discord_id=None, discord_name=None, twitch_name=None, rtmp_name=None, user_id=None):
        if discord_id is None and discord_name is None and twitch_name is None \
                and rtmp_name is None and user_id is None:
            raise RuntimeError('Error: Called NecroUser.get_user with no non-None fields.')

        raw_db_data = necrodb.get_all_users(
            discord_id=discord_id,
            discord_name=discord_name,
            twitch_name=twitch_name,
            rtmp_name=rtmp_name,
            user_id = user_id
        )

        if not raw_db_data:
            return None
        elif len(raw_db_data) > 1:
            raise DuplicateUserException(
                'Two or more users found satisfying discord_id={0}, discord_name={1}, twitch_name={2}, '
                'rtmp_name={3}.'.format(discord_id, discord_name, twitch_name, rtmp_name))

        for row in raw_db_data:
            member = necrobot.find_member(discord_id=int(row[0]))
            if member is None:
                return None

            user = NecroUser(member)
            user.twitch_name = row[2]
            user.rtmp_name = row[3]
            user.set_timezone(row[4])
            user.user_info = row[5]
            user.user_prefs = UserPrefs()
            user.user_prefs.daily_alert = bool(row[6])
            user.user_prefs.race_alert = bool(row[7])
            user.user_id = int(row[8])
            return user

    def __init__(self, discord_member):
        self.user_id = None
        self.member = discord_member
        self.twitch_name = None
        self.rtmp_name = None
        self._timezone = None
        self.user_info = None
        self.user_prefs = None

    def __eq__(self, other):
        return self.discord_id == other.discord_id

    @property
    def timezone(self):
        return self._timezone

    @property
    def discord_id(self):
        return self.member.id

    @property
    def discord_name(self):
        return self.member.display_name

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

    def set_timezone(self, name):
        if name is None:
            return
        elif name not in pytz.common_timezones:
            console.error('Tried to set timezone to {0}.'.format(name))
            self._timezone = None
        else:
            self._timezone = pytz.timezone(name)
