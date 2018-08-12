import asyncio
import discord
import pytz
import re
import textwrap
import unittest
from typing import Callable

from necrobot.botbase import server
from necrobot.stats.leaguestats import LeagueStats
from necrobot.util import console, strutil

from necrobot.user.userprefs import UserPrefs


class NecroUser(object):
    def __init__(self, commit_fn):
        """Initialization. There should be no reason to directly create NecroUser objects; use userlib 
        instead.
        
        Parameters
        ----------
        commit_fn: function(NecroUser) -> None
            This should write the NecroUser to the database.
        """
        self._user_id = None            # type: int
        self._discord_id = None         # type: int
        self._discord_name = None       # type: str
        self._discord_member = None     # type: discord.Member
        self._twitch_name = None        # type: str
        self._rtmp_name = None          # type: str
        self._timezone = None           # type: pytz.timezone
        self._user_info = None          # type: str
        self._user_prefs = UserPrefs(daily_alert=False, race_alert=False)   # type: UserPrefs

        self._commit = commit_fn        # type: Callable[None, None]

    def __eq__(self, other):
        return self.user_id == other.user_id

    def __repr__(self):
        if self.rtmp_name is not None:
            name_str = 'RTMP: ' + self.rtmp_name
        elif self.discord_name is not None:
            name_str = 'Discord: ' + self.discord_name
        elif self.twitch_name is not None:
            name_str = 'Twitch: ' + self.twitch_name
        else:
            name_str = '<unnamed>'
        return 'User {uid} ({name})'.format(uid=self._user_id, name=name_str)

    def __str__(self):
        return self.display_name

    async def commit(self) -> None:
        await self._commit(self)

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
    def discord_id(self) -> int:
        return self.discord_member.id if self.discord_member is not None else self._discord_id

    @property
    def discord_member(self) -> discord.Member or None:
        if self._discord_member is None and \
                (self._discord_id is not None or self._discord_name is not None):
            self._discord_member = server.find_member(discord_name=self._discord_name, discord_id=self._discord_id)
        return self._discord_member

    @property
    def discord_name(self) -> str:
        return self.discord_member.display_name if self.discord_member is not None else self._discord_name

    @property
    def display_name(self) -> str:
        if self.discord_name is not None:
            return self.rtmp_name
        elif self.rtmp_name is not None:
            return self.discord_name
        elif self.twitch_name is not None:
            return self.twitch_name
        else:
            return '<NecroUser with ID {}>'.format(self.user_id)

    @property
    def gsheet_name(self):
        return self.twitch_name

    @property
    def member(self) -> discord.Member or None:
        return self.discord_member

    @property
    def rtmp_name(self) -> str:
        return self._rtmp_name

    @property
    def timezone(self) -> pytz.timezone:
        return self._timezone

    @property
    def timezone_str(self) -> str or None:
        return str(self._timezone) if self._timezone is not None else None

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
               '{1}```'\
                .format(
                    strutil.tickless(self.infoname),
                    strutil.tickless(self.infotext)
                )

    def set(
        self,
        discord_member: discord.Member = None,
        discord_id: int = None,
        discord_name: str = None,
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
        discord_id: int
            The user's discord ID. Not necessary if discord_member is not None.
        discord_name: str
            The user's discord name. Not necessary if discord_member is not None.
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
        if discord_member is not None and discord_member != self.discord_member:
            self._discord_id = int(discord_member.id)
            self._discord_name = discord_member.display_name
            self._discord_member = discord_member
            changed_any = True
        elif discord_id is not None and discord_id != self.discord_id:
            self._discord_id = discord_id
            member = server.find_member(discord_id=discord_id)
            if member is not None:
                self._discord_member = member
                self._discord_name = member.display_name
            elif discord_name is not None:
                self._discord_name = discord_name
            changed_any = True
        elif discord_name is not None and discord_name != self.discord_name:
            self._discord_name = discord_name
            member = server.find_member(discord_name=discord_name)
            if member is not None:
                self._discord_member = member
                self._discord_id = int(member.id)
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
            self._user_prefs.merge_prefs(user_prefs)
            changed_any = True

        if changed_any and commit:
            asyncio.ensure_future(self.commit())

    async def get_big_infotext(self, stats: LeagueStats) -> str:
        return textwrap.dedent(
            """
            {discord_name} ({userinfo})
                   RTMP: {rtmp_name}
                 Twitch: {twitch_name}
               Timezone: {timezone}
                 Record: {wins}-{losses}
               Best win: {best_win}
               Avg. win: {avg_win}
            """
            .format(
                discord_name=self.discord_name,
                userinfo=self.user_info,
                rtmp_name=self.rtmp_name,
                twitch_name=self.twitch_name,
                timezone=self.timezone,
                wins=stats.wins,
                losses=stats.losses,
                best_win=stats.best_win_str,
                avg_win=stats.avg_win_str
            )
        )


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
