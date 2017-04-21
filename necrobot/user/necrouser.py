import pytz

from necrobot.database import necrodb
from necrobot.util import console
from necrobot.util import strutil


class NecroUser(object):
    def __init__(self, discord_member=None, rtmp_name=None):
        self.user_id = None
        self.member = discord_member
        self.twitch_name = None
        self.rtmp_name = rtmp_name
        self._timezone = None
        self.user_info = None
        self.user_prefs = None

    def __eq__(self, other):
        return self.discord_id == other.discord_id

    def commit(self):
        necrodb.write_user(self)

    @property
    def timezone(self):
        return self._timezone

    @property
    def discord_id(self):
        return self.member.id if self.member else None

    @property
    def discord_name(self):
        return self.member.display_name if self.member else None

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
