import asyncio
import datetime
import unittest
from typing import Optional

import league.leagueutil
import necrobot.exception
from necrobot.botbase.necroevent import NEDispatch, NecroEvent
from necrobot.botbase.manager import Manager
from necrobot.config import Config
from necrobot.condorbot import condordb
from necrobot.database import dbutil
from necrobot.gsheet import sheetlib
from necrobot.gsheet.matchupsheet import MatchupSheet
from necrobot.gsheet.standingssheet import StandingsSheet
from necrobot.gsheet.speedrunsheet import SpeedrunSheet
from necrobot.league.leaguemgr import LeagueMgr
from necrobot.league import leaguestats
from necrobot.match import matchutil
from necrobot.match.match import Match
from necrobot.match.matchglobals import MatchGlobals
from necrobot.util import console, server, strutil, rtmputil
from necrobot.util.parse import dateparse
from necrobot.util.singleton import Singleton

print('import cmgr')


class CondorMgr(Manager, metaclass=Singleton):
    """Manager object for the CoNDOR Events server"""
    def __init__(self):
        self._main_channel = None
        self._notifications_channel = None
        self._schedule_channel = None
        self._client = None
        self._event = None
        NEDispatch().subscribe(self)

    async def initialize(self):
        self._main_channel = server.find_channel(channel_name=Config.MAIN_CHANNEL_NAME)
        self._notifications_channel = server.find_channel(channel_name=Config.NOTIFICATIONS_CHANNEL_NAME)
        self._schedule_channel = server.find_channel(channel_name=Config.SCHEDULE_CHANNEL_NAME)
        self._client = server.client

        if Config.LEAGUE_NAME:
            try:
                await self.set_event(Config.LEAGUE_NAME)
                console.info('Event recovered: "{0}"'.format(self._event.schema_name))
            except necrobot.exception.SchemaDoesNotExist:
                console.warning('League "{0}" does not exist.'.format(Config.LEAGUE_NAME))
        else:
            console.warning('No league given in Config.')

        # TODO: this has to be done after matches are initted, otherwise it's useless!
        # await self._update_schedule_channel()

    async def refresh(self):
        self._notifications_channel = server.find_channel(channel_name=Config.NOTIFICATIONS_CHANNEL_NAME)
        self._schedule_channel = server.find_channel(channel_name=Config.SCHEDULE_CHANNEL_NAME)
        self._client = server.client
        await self._update_schedule_channel()

    async def close(self):
        pass

    def on_botchannel_create(self, channel, bot_channel):
        pass

    async def ne_process(self, ev: NecroEvent):
        if ev.event_type == 'begin_match_race':
            pass
            # asyncio.ensure_future(VodRecorder().start_record(ev.match.racer_1.rtmp_name))
            # asyncio.ensure_future(VodRecorder().start_record(ev.match.racer_2.rtmp_name))

        elif ev.event_type == 'end_match':
            async def send_mainchannel_message():
                await self._main_channel.send(
                    'Match complete: **{r1}** [{w1}-{w2}] **{r2}** :tada:'.format(
                        r1=ev.match.racer_1.display_name,
                        r2=ev.match.racer_2.display_name,
                        w1=ev.r1_wins,
                        w2=ev.r2_wins
                    )
                )

            asyncio.ensure_future(self._overwrite_gsheet())
            asyncio.ensure_future(send_mainchannel_message())

        elif ev.event_type == 'end_match_race':
            pass
            # asyncio.ensure_future(VodRecorder().end_record(ev.match.racer_1.rtmp_name))
            # asyncio.ensure_future(VodRecorder().end_record(ev.match.racer_2.rtmp_name))

        elif ev.event_type == 'match_alert':
            if ev.final:
                await self._match_alert(ev.match)
            else:
                await self._cawmentator_alert(ev.match)

        elif ev.event_type == 'notify':
            if self._notifications_channel is not None:
                await self._notifications_channel.send(ev.message)

        elif ev.event_type == 'create_match':
            pass

        elif ev.event_type == 'delete_match':
            pass

        elif ev.event_type == 'schedule_match':
            asyncio.ensure_future(self._overwrite_gsheet())
            asyncio.ensure_future(self._update_schedule_channel())

        elif ev.event_type == 'set_cawmentary':
            asyncio.ensure_future(self._overwrite_gsheet())

        elif ev.event_type == 'set_vod':
            asyncio.ensure_future(self._overwrite_gsheet())
            cawmentator = await ev.match.get_cawmentator()
            await self._main_channel.send(
                '{cawmentator} added a vod for **{r1}** - **{r2}**: <{url}>'.format(
                    cawmentator=cawmentator.display_name if cawmentator is not None else '<unknown>',
                    r1=ev.match.racer_1.display_name,
                    r2=ev.match.racer_2.display_name,
                    url=ev.url
                )
            )

        elif ev.event_type == 'submitted_run':
            asyncio.ensure_future(self._overwrite_speedrun_sheet())

    @property
    def has_event(self):
        return self._event.schema_name is not None

    @property
    def event(self):
        return self._event

    async def create_event(self, schema_name: str, save_to_config=True):
        """Registers a new CoNDOR event

        Parameters
        ----------
        schema_name: str
            The schema name for the event
        save_to_config: bool
            Whether to make this the default event, i.e., save the schema name to the bot's config file

        Raises
        ------
        necrobot.database.leaguedb.SchemaAlreadyExists
            If the schema name already exists in the database
        necrobot.database.leaguedb.InvalidSchemaName
            If the schema name is not a valid MySQL schema name
        """
        self._event = await condordb.create_event(schema_name)
        dbutil.league_schema_name = schema_name

        if save_to_config:
            Config.LEAGUE_NAME = schema_name
            Config.write()

    async def set_event(self, schema_name: str, save_to_config=True):
        """Set the current CoNDOR event

        Parameters
        ----------
        schema_name: str
            The schema name for the league
        save_to_config: bool
            Whether to make this the default league, i.e., save the schema name to the bot's config file

        Raises
        ------
        necrobot.database.leaguedb.LeagueDoesNotExist
            If the schema name does not refer to a registered league
        """
        if not await condordb.is_condor_event(Config.LEAGUE_NAME):
            raise necrobot.exception.SchemaDoesNotExist('Schema "{0}" does not exist.'.format(schema_name))

        self._event = await condordb.get_event(schema_name=schema_name)
        dbutil.league_schema_name = schema_name
        MatchGlobals().set_deadline_fn(lambda: self.deadline())

        if save_to_config:
            Config.LEAGUE_NAME = schema_name
            Config.write()

    async def set_deadline(self, deadline_str):
        await condordb.set_event_params(self._event.schema_name, deadline=deadline_str)
        self._event.deadline_str = deadline_str

    async def set_event_name(self, event_name):
        await condordb.set_event_params(self._event.schema_name, event_name=event_name)
        self._event.event_name = event_name

    @property
    def schema_name(self) -> Optional[str]:
        return self._event.schema_name

    @property
    def deadline_str(self) -> Optional[str]:
        return self._event.deadline_str

    def deadline(self) -> Optional[datetime.datetime]:
        if self._event.deadline_str is not None:
            return dateparse.parse_datetime(self._event.deadline_str)
        return None

    async def _overwrite_gsheet(self):
        # noinspection PyShadowingNames
        sheet = await self._get_gsheet(wks_id='0')
        await sheet.overwrite_gsheet()

    @staticmethod
    async def _overwrite_speedrun_sheet():
        speedrun_sheet = await sheetlib.get_sheet(
            gsheet_id=LeagueMgr().league.speedrun_gsheet_id,
            wks_id='0',
            sheet_type=sheetlib.SheetType.SPEEDRUN
        )  # type: SpeedrunSheet
        await speedrun_sheet.overwrite_gsheet()

    @staticmethod
    async def _get_gsheet(wks_id: str) -> MatchupSheet:
        return await sheetlib.get_sheet(
            gsheet_id=LeagueMgr().league.gsheet_id,
            wks_id=wks_id,
            sheet_type=sheetlib.SheetType.MATCHUP
        )

    @staticmethod
    async def _get_standings_sheet() -> StandingsSheet:
        return await sheetlib.get_sheet(
            gsheet_id=LeagueMgr().league.gsheet_id,
            wks_name='Standings',
            sheet_type=sheetlib.SheetType.STANDINGS
        )

    @staticmethod
    async def _cawmentator_alert(match: Match):
        """PM an alert to the match cawmentator, if any, that the match is soon to begin
        
        Parameters
        ----------
        match: Match
        """
        # PM a cawmentator alert
        cawmentator = await match.get_cawmentator()
        if cawmentator is None or match.time_until_match is None:
            return

        alert_format_str = 'Reminder: You\'re scheduled to cawmentate **{racer_1}** - **{racer_2}**, ' \
                           'which is scheduled to begin in {minutes} minutes.\n\n'
        alert_text = alert_format_str.format(
            racer_1=match.racer_1.display_name,
            racer_2=match.racer_2.display_name,
            minutes=int((match.time_until_match.total_seconds() + 30) // 60)
        )

        racer_1_stats = await leaguestats.get_league_stats(match.racer_1.user_id)
        racer_2_stats = await leaguestats.get_league_stats(match.racer_2.user_id)

        racer_1_infotext = await leaguestats.get_big_infotext(user=match.racer_1, stats=racer_1_stats)
        racer_2_infotext = await leaguestats.get_big_infotext(user=match.racer_2, stats=racer_2_stats)
        alert_text += '```' + strutil.tickless(racer_1_infotext) + '\n```'
        alert_text += '```' + strutil.tickless(racer_2_infotext) + '\n```'

        await cawmentator.member.send(alert_text)

    async def _match_alert(self, match: Match) -> None:
        """Post an alert that the match is about to begin in the main channel
        
        Parameters
        ----------
        match: Match
        """
        alert_format_str = "The match **{racer_1}** - **{racer_2}** is scheduled to begin in {minutes} " \
                           "minutes. :timer: \n" \
                           "{stream}"

        minutes_until_match = int((match.time_until_match.total_seconds() + 30) // 60)
        cawmentator = await match.get_cawmentator()
        if cawmentator is not None:
            stream = 'Cawmentary: <http://www.twitch.tv/{0}>'.format(cawmentator.twitch_name)
        else:
            stream = 'Kadgar: {}'.format(rtmputil.kadgar_link(match.racer_1.twitch_name, match.racer_2.twitch_name))

        await self._main_channel.send(
            alert_format_str.format(
                racer_1=match.racer_1.display_name,
                racer_2=match.racer_2.display_name,
                minutes=minutes_until_match,
                stream=stream
            )
        )

    async def _update_schedule_channel(self):
        infotext = await league.leagueutil.get_schedule_infotext()

        # Find the message:
        the_msg = None
        async for msg in self._schedule_channel.history():
            if msg.author.id == server.client.user.id:
                the_msg = msg
                break

        if the_msg is None:
            await self._schedule_channel.send(infotext)
        else:
            await the_msg.edit(content=infotext)


class TestCondorMgr(unittest.TestCase):
    from necrobot.test.asynctest import async_test

    loop = asyncio.new_event_loop()
    fake_match = None

    @classmethod
    def setUpClass(cls):
        import datetime
        from necrobot.test import testmatch

        utcnow = datetime.datetime.utcnow()

        cls.fake_match = TestCondorMgr.loop.run_until_complete(testmatch.get_match(
            r1_name='incnone',
            r2_name='incnone_testing',
            time=utcnow + datetime.timedelta(minutes=5),
            cawmentator_name='incnone'
        ))

    @classmethod
    def tearDownClass(cls):
        cls.loop.close()

    @async_test(asyncio.get_event_loop())
    async def test_cawmentary_pm(self):
        await CondorMgr()._cawmentator_alert(self.fake_match)
