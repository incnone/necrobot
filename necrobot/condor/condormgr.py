import asyncio
import unittest

from necrobot.botbase import server
from necrobot.condor import cmd_condor
from necrobot.gsheet import cmd_sheet
from necrobot.match import matchutil
from necrobot.gsheet import sheetlib
from necrobot.stats import statfn
from necrobot.user import userlib

from necrobot.botbase.manager import Manager
from necrobot.gsheet.matchupsheet import MatchupSheet
from necrobot.gsheet.standingssheet import StandingsSheet
from necrobot.league.leaguemgr import LeagueMgr
from necrobot.match.match import Match
from necrobot.match.matchroom import MatchRoom
from necrobot.necroevent.necroevent import NEDispatch, NecroEvent
from necrobot.stream.vodrecord import VodRecorder
from necrobot.util.singleton import Singleton


class CondorMgr(Manager, metaclass=Singleton):
    """Manager object for the CoNDOR Events server"""
    def __init__(self):
        self._main_channel = None
        self._notifications_channel = None
        self._schedule_channel = None
        self._client = None
        NEDispatch().subscribe(self)

    async def initialize(self):
        self._main_channel = server.main_channel
        self._notifications_channel = server.find_channel(channel_name='bot_notifications')
        self._schedule_channel = server.find_channel(channel_name='schedule')
        self._client = server.client

        await self.update_schedule_channel()

    async def refresh(self):
        self._notifications_channel = server.find_channel(channel_name='bot_notifications')
        self._schedule_channel = server.find_channel(channel_name='schedule')
        self._client = server.client
        await self.update_schedule_channel()

    async def close(self):
        pass

    def on_botchannel_create(self, channel, bot_channel):
        bot_channel.default_commands.append(cmd_condor.StaffAlert(bot_channel))
        if isinstance(bot_channel, MatchRoom):
            bot_channel.default_commands.append(cmd_sheet.PushMatchToSheet(bot_channel))

    async def ne_process(self, ev: NecroEvent):
        if ev.event_type == 'begin_match_race':
            await VodRecorder().start_record(ev.match.racer_1.rtmp_name)
            await VodRecorder().start_record(ev.match.racer_2.rtmp_name)
        elif ev.event_type == 'end_match':
            sheet = await self.get_gsheet(wks_id=ev.match.sheet_id)
            await sheet.record_score(
                match=ev.match,
                winner=ev.winner,
                winner_wins=ev.winner_wins,
                loser_wins=ev.loser_wins
            )
            standings = await self.get_standings_sheet()
            await standings.update_standings(
                match=ev.match,
                r1_wins=ev.r1_wins,
                r2_wins=ev.r2_wins
            )
            await server.client.send_message(
                self._main_channel,
                'Match complete: **{r1}** [{w1}-{w2}] **{r2}** :tada:'.format(
                    r1=ev.match.racer_1.display_name,
                    r2=ev.match.racer_2.display_name,
                    w1=ev.r1_wins,
                    w2=ev.r2_wins
                )
            )
        elif ev.event_type == 'end_match_race':
            await VodRecorder().end_record(ev.match.racer_1.rtmp_name)
            await VodRecorder().end_record(ev.match.racer_2.rtmp_name)
        elif ev.event_type == 'match_alert':
            if ev.final:
                await self.match_alert(ev.match)
            else:
                await self.cawmentator_alert(ev.match)
        elif ev.event_type == 'notify':
            if self._notifications_channel is not None:
                await self._client.send_message(self._notifications_channel, ev.message)
        elif ev.event_type == 'schedule_match':
            sheet = await self.get_gsheet(wks_id=ev.match.sheet_id)
            await sheet.schedule_match(ev.match)
            await self.update_schedule_channel()
        elif ev.event_type == 'set_cawmentary':
            if ev.match.sheet_id is not None:
                sheet = await self.get_gsheet(wks_id=ev.match.sheet_id)
                await sheet.set_cawmentary(match=ev.match)
        elif ev.event_type == 'set_vod':
            if ev.match.sheet_id is not None:
                sheet = await self.get_gsheet(wks_id=ev.match.sheet_id)
                await sheet.set_vod(match=ev.match, vod_link=ev.url)

    @staticmethod
    async def get_gsheet(wks_id: str) -> MatchupSheet:
        return await sheetlib.get_sheet(
            gsheet_id=LeagueMgr().league.gsheet_id,
            wks_id=wks_id,
            sheet_type=sheetlib.SheetType.MATCHUP
        )

    @staticmethod
    async def get_standings_sheet() -> StandingsSheet:
        return await sheetlib.get_sheet(
            gsheet_id=LeagueMgr().league.gsheet_id,
            wks_name='Standings',
            sheet_type=sheetlib.SheetType.STANDINGS
        )

    async def cawmentator_alert(self, match: Match):
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

        racer_1_stats = await statfn.get_league_stats(match.racer_1.user_id)
        racer_2_stats = await statfn.get_league_stats(match.racer_2.user_id)

        alert_text += '```' + await match.racer_1.get_big_infotext(racer_1_stats) + '\n```'
        alert_text += '```' + await match.racer_2.get_big_infotext(racer_2_stats) + '\n```'

        await self._client.send_message(cawmentator.member, alert_text)

    async def match_alert(self, match: Match) -> None:
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
            stream = 'RTMP: <http://rtmp.condorleague.tv/#{0}/{1}>'.format(
                match.racer_1.rtmp_name,
                match.racer_2.rtmp_name
            )

        await self._client.send_message(
            self._main_channel,
            alert_format_str.format(
                racer_1=match.racer_1.display_name,
                racer_2=match.racer_2.display_name,
                minutes=minutes_until_match,
                stream=stream
            )
        )

    async def update_schedule_channel(self):
        infotext = await matchutil.get_schedule_infotext()

        # Find the message:
        the_msg = None
        async for msg in server.client.logs_from(self._schedule_channel):
            if msg.author.id == server.client.user.id:
                the_msg = msg
                break

        if the_msg is None:
            await server.client.send_message(
                self._schedule_channel,
                infotext
            )
        else:
            await server.client.edit_message(
                message=the_msg,
                new_content=infotext
            )


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
        await CondorMgr().cawmentator_alert(self.fake_match)
