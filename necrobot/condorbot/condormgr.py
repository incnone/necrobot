import asyncio
import datetime
import unittest
from typing import Optional

import necrobot.exception
from necrobot.botbase.necroevent import NEDispatch, NecroEvent
from necrobot.botbase.manager import Manager
from necrobot.config import Config
from necrobot.condorbot import condordb
from necrobot.database import dbutil
from necrobot.gsheet import sheetlib
from necrobot.gsheet.matchupsheet import MatchupSheet
from necrobot.gsheet.standingssheet import StandingsSheet
from necrobot.league.leaguemgr import LeagueMgr
from necrobot.league import leaguestats
from necrobot.league import leagueutil
from necrobot.league.league import League
from necrobot.match.match import Match
from necrobot.match.matchroom import MatchRoom
from necrobot.match import matchchannelutil
from necrobot.match.matchglobals import MatchGlobals
from necrobot.util import console, server, strutil, rtmputil
from necrobot.util.necrodancer import emotes
from necrobot.util.parse import dateparse
from necrobot.util.singleton import Singleton


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
        self._main_channel = server.find_channel(channel_id=Config.MAIN_CHANNEL_ID)
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
                    'Match complete: {em}**{r1}** [{w1}-{w2}] **{r2}** :tada:'.format(
                        em=emotes.get_emote_str(ev.match.league_tag),
                        r1=ev.match.racer_1.display_name,
                        r2=ev.match.racer_2.display_name,
                        w1=ev.r1_wins,
                        w2=ev.r2_wins
                    )
                )

            try:
                league = await LeagueMgr().get_league(ev.match.league_tag)
                asyncio.ensure_future(self._overwrite_gsheet(league=league))
            except necrobot.exception.LeagueDoesNotExist:
                pass
            asyncio.ensure_future(self._overwrite_schedule_gsheet())
            asyncio.ensure_future(send_mainchannel_message())

            matchroom = await matchchannelutil.get_match_room(ev.match)  # type: Optional[MatchRoom]
            if matchroom is not None:
                await matchroom.remove_cawmentator_permissions()

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
            asyncio.ensure_future(self._overwrite_schedule_gsheet())

        elif ev.event_type == 'unschedule_match':
            await self._cawmentator_alert_unschedule(ev.match)

        elif ev.event_type == 'set_cawmentary':
            asyncio.ensure_future(self._overwrite_schedule_gsheet())
            if not ev.add:
                matchroom = await matchchannelutil.get_match_room(ev.match)  # type: Optional[MatchRoom]
                if matchroom is not None:
                    await matchroom.remove_cawmentator_permissions()

        elif ev.event_type == 'set_vod':
            asyncio.ensure_future(self._overwrite_schedule_gsheet())
            cawmentator = await ev.match.get_cawmentator()
            await self._main_channel.send(
                '{cawmentator} added a vod for {em}**{r1}** - **{r2}**: <{url}>'.format(
                    cawmentator=cawmentator.display_name if cawmentator is not None else '<unknown>',
                    em=emotes.get_emote_str(ev.match.league_tag),
                    r1=ev.match.racer_1.display_name,
                    r2=ev.match.racer_2.display_name,
                    url=ev.url
                )
            )

        # elif ev.event_type == 'submitted_run':
        #     asyncio.ensure_future(self._overwrite_speedrun_sheet())

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

    async def set_gsheet_id(self, gsheet_id):
        await condordb.set_event_params(self._event.schema_name, gsheet_id=gsheet_id)
        self._event.gsheet_id = gsheet_id

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

    async def _overwrite_gsheet(self, league: League):
        # noinspection PyShadowingNames
        sheet = await self._get_gsheet(league=league)
        await sheet.overwrite_gsheet(league.tag)

    async def _overwrite_schedule_gsheet(self):
        # noinspection PyShadowingNames
        sheet = await self._get_schedule_gsheet()
        await sheet.overwrite_gsheet()

    # @staticmethod
    # async def _overwrite_speedrun_sheet(league: League):
    #     speedrun_sheet = await sheetlib.get_sheet(
    #         gsheet_id=league.speedrun_gsheet_id,
    #         wks_id='0',
    #         sheet_type=sheetlib.SheetType.SPEEDRUN
    #     )  # type: SpeedrunSheet
    #     await speedrun_sheet.overwrite_gsheet()

    # async def _get_gsheet(self, league: League) -> MatchupSheet:
    #     return None
    #     return await sheetlib.get_sheet(
    #         gsheet_id=self._event.gsheet_id,
    #         wks_id=league.worksheet_id,
    #         sheet_type=sheetlib.SheetType.MATCHUP
    #     )

    async def _get_gsheet(self, league: League) -> StandingsSheet:
        return await sheetlib.get_sheet(
            gsheet_id=self._event.gsheet_id,
            wks_id=league.worksheet_id,
            sheet_type=sheetlib.SheetType.STANDINGS
        )

    async def _get_schedule_gsheet(self) -> MatchupSheet:
        return await sheetlib.get_sheet(
            gsheet_id=self._event.gsheet_id,
            wks_id=0,                                   # TODO: hack
            sheet_type=sheetlib.SheetType.MATCHUP
        )

    @staticmethod
    async def _cawmentator_alert_unschedule(match: Match):
        """PM an alert to the match cawmentator, if any, that the previously scheduled match has been unscheduled

        Parameters
        ----------
        match: Match
        """
        # PM a cawmentator alert
        cawmentator = await match.get_cawmentator()
        if cawmentator is None:
            return

        alert_format_str = 'A race you\'re scheduled to cawmentate has been unscheduled. ' \
                           '(**{racer_1}** - **{racer_2}**)\n' \
                           '(Note: You are still the cawmentator for this race. If the racers ' \
                           'reschedule to a time that doesn\'t work for you, use .uncawmentate)\n\n'

        alert_text = alert_format_str.format(
            racer_1=match.racer_1.display_name,
            racer_2=match.racer_2.display_name
        )

        await cawmentator.member.send(alert_text)

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
                           'which is scheduled to begin {timestamp}.\n\n'
        alert_text = alert_format_str.format(
            racer_1=match.racer_1.display_name,
            racer_2=match.racer_2.display_name,
            timestamp=match.discord_rel_timestamp
        )

        league_tag = match.league_tag
        try:
            await LeagueMgr().get_league(league_tag=league_tag)
            racer_1_stats = await leaguestats.get_league_stats(league_tag=league_tag, user_id=match.racer_1.user_id)
            racer_2_stats = await leaguestats.get_league_stats(league_tag=league_tag, user_id=match.racer_2.user_id)

            racer_1_infotext = await leaguestats.get_big_infotext(user=match.racer_1, stats=racer_1_stats)
            racer_2_infotext = await leaguestats.get_big_infotext(user=match.racer_2, stats=racer_2_stats)
            alert_text += '```' + strutil.tickless(racer_1_infotext) + '\n```'
            alert_text += '```' + strutil.tickless(racer_2_infotext) + '\n```'
        except necrobot.exception.LeagueDoesNotExist:
            pass

        await cawmentator.member.send(alert_text)

    async def _match_alert(self, match: Match) -> None:
        """Post an alert that the match is about to begin in the main channel
        
        Parameters
        ----------
        match: Match
        """
        alert_format_str = "The match {em}**{racer_1}** - **{racer_2}** is scheduled to begin {timestamp}. :timer: \n" \
                           "{stream}"

        cawmentator = await match.get_cawmentator()
        if cawmentator is not None:
            stream = 'Cawmentary: <http://www.twitch.tv/{0}>'.format(cawmentator.twitch_name)
        else:
            stream = 'Kadgar: {}'.format(rtmputil.kadgar_link(match.racer_1.twitch_name, match.racer_2.twitch_name))

        await self._main_channel.send(
            alert_format_str.format(
                em=emotes.get_emote_str(match.league_tag),
                racer_1=match.racer_1.display_name,
                racer_2=match.racer_2.display_name,
                timestamp=match.discord_rel_timestamp,
                stream=stream
            )
        )

        matchroom = await matchchannelutil.get_match_room(match)    # type: Optional[MatchRoom]
        if matchroom is not None:
            await matchroom.add_cawmentator_permissions()

    async def _update_schedule_channel(self):
        pass
        # infotext = await leagueutil.get_schedule_infotext()
        #
        # # Find the message:
        # the_msg = None
        # async for msg in self._schedule_channel.history():
        #     if msg.author.id == server.client.user.id:
        #         the_msg = msg
        #         break
        #
        # if the_msg is None:
        #     await self._schedule_channel.send(infotext)
        # else:
        #     await the_msg.edit(content=infotext)


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
