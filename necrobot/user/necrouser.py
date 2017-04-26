import asyncio
import datetime
import discord
import pytz
import re
import unittest

from necrobot.util import console
from necrobot.util import strutil

from necrobot.user.userprefs import UserPrefs


class NecroUser(object):
    def __init__(self, commit_fn):
        """Initialization. There should be no reason to directly create NecroUser objects; use userutil.get_user 
        instead.
        
        Parameters
        ----------
        commit_fn: function(NecroUser) -> None
            This should write the NecroUser to the database.
        """
        self._user_id = None
        self._discord_member = None
        self._twitch_name = None
        self._rtmp_name = None
        self._timezone = None
        self._user_info = None
        self._user_prefs = UserPrefs()

        self._commit = commit_fn

    def __eq__(self, other):
        return self.user_id == other.user_id

    def commit(self):
        asyncio.ensure_future(self._commit(self))

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def name_regex(self):
        """A compiled Regular Expression Object matching the racer's various names"""
        re_str = r''
        if self.rtmp_name is not None:
            re_str += re.escape(self.rtmp_name) + r'|'
        if self.discord_name is not None:
            re_str += re.escape(self.discord_name) + r'|'
        if self.twitch_name is not None:
            re_str += re.escape(self.twitch_name) + r'|'

        if re_str == r'':
            return None

        re_str = re_str[:-1]

        return re.compile(r'(?i)^\s*(' + re_str + r')\s*$')

    @property
    def bot_name(self) -> str:
        if self.rtmp_name is not None:
            return self.rtmp_name
        elif self.discord_name is not None:
            return self.discord_name
        elif self.twitch_name is not None:
            return self.twitch_name
        else:
            console.warning('User with no name: ID <{}>.'.format(self.user_id))
            return '<Unknown user>.'

    @property
    def discord_id(self) -> int:
        return self.discord_member.id if self.discord_member is not None else None

    @property
    def discord_member(self) -> discord.Member:
        return self._discord_member

    @property
    def discord_name(self) -> str:
        return self.discord_member.display_name if self.discord_member is not None else None

    @property
    def display_name(self) -> str:
        return self.bot_name

    @property
    def member(self) -> discord.Member:
        return self._discord_member

    @property
    def rtmp_name(self) -> str:
        return self._rtmp_name

    @property
    def timezone(self) -> datetime.datetime:
        return self._timezone

    @property
    def timezone_str(self) -> str:
        return str(self._timezone)

    @property
    def twitch_name(self) -> str:
        return self._twitch_name

    @property
    def user_info(self) -> str:
        return self._user_info

    @property
    def user_prefs(self) -> UserPrefs:
        return self._user_prefs

    @property
    def infoname(self) -> str:
        if self.user_info is not None:
            return '{0} ({1})'.format(self.discord_name, self.user_info)
        else:
            return self.discord_name

    @property
    def infotext(self) -> str:
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
    def infobox(self) -> str:
        return '```\n' \
               '{0}\n' \
               '{1}```'.format(
                    self.infoname,
                    self.infotext)

    @property
    def escaped_twitch_name(self) -> str:
        return strutil.escaped(self.twitch_name)

    @property
    def escaped_rtmp_name(self) -> str:
        return strutil.escaped(self.rtmp_name)

    def set_user_id(self, user_id):
        """
        Parameters
        ----------
        user_id: int
            The user's database ID. Called by userutil during creation.
        """
        self._user_id = user_id

    def set(self,
            discord_member: discord.Member = None,
            twitch_name: str = None,
            rtmp_name: str = None,
            timezone: str = None,
            user_info: str = None,
            user_prefs: UserPrefs = None,
            commit: bool = True
            ) -> None:
        """Set all non-None values and optionally commit the change to the database.
        
        Parameters
        ----------
        discord_member: discord.Member
            The discord.Member corresponding to this necrobot user.
        twitch_name: str
            This user's twitch name. Case-insensitive.
        rtmp_name: str
            This user's RTMP name. Case-insensitive.
        timezone: str
            The user's timezone as a string, e.g., 'Asia/Tokyo'.
        user_info: str
            The user's custom info (shown on .userinfo).
        user_prefs: UserPrefs  
            The user's preferences.
        commit: bool
            If False, will not commit changes to the database.
        """

        changed_any = False
        if discord_member is not None and discord_member != self._discord_member:
            self._discord_member = discord_member
            changed_any = True
        if twitch_name is not None and twitch_name != self._twitch_name:
            self._twitch_name = twitch_name
            changed_any = True
        if rtmp_name is not None and rtmp_name != self._rtmp_name:
            self._rtmp_name = rtmp_name
            changed_any = True
        if timezone is not None:
            if timezone not in pytz.common_timezones:
                console.warning('Tried to set timezone to {0}.'.format(timezone))
            elif str(self.timezone) != timezone:
                self._timezone = pytz.timezone(timezone)
                changed_any = True
        if user_info is not None and user_info != self._user_info:
            self._user_info = user_info
            changed_any = True
        if user_prefs is not None and user_prefs != self._user_prefs:
            self._user_prefs = user_prefs
            changed_any = True

        if changed_any and commit:
            self.commit()


class TestNecroUser(unittest.TestCase):
    def setUp(self):
        def commit_fn(_):
            pass
        self.commit_fn = commit_fn

    def test_regex(self):
        user_1 = NecroUser(self.commit_fn)
        user_1.set(
            rtmp_name='incnone RTMP',
            twitch_name='incnone_twitch',
            commit=False
        )
        self.assertTrue(user_1.name_regex.match(' incnone rtmp '))
        self.assertTrue(user_1.name_regex.match(' Incnone_Twitch '))
        self.assertFalse(user_1.name_regex.match('incnone_nomatch'))
