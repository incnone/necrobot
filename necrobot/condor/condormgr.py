from necrobot.condor import cmd_condor
from necrobot.gsheet import cmd_sheet
from necrobot.match import matchutil
from necrobot.gsheet import sheetlib
from necrobot.stats import statfn
from necrobot.user import userutil

from necrobot.league.leaguemgr import LeagueMgr
from necrobot.match.match import Match
from necrobot.match.matchroom import MatchRoom
from necrobot.botbase.necrobot import Necrobot
from necrobot.necroevent.necroevent import NEDispatch, NecroEvent
from necrobot.stream.vodrecord import VodRecorder
from necrobot.util.singleton import Singleton


class CondorMgr(object, metaclass=Singleton):
    """Manager object for the CoNDOR Events server"""
    def __init__(self):
        self._main_channel = None
        self._notifications_channel = None
        self._schedule_channel = None
        self._client = None
        NEDispatch().subscribe(self)

    async def initialize(self):
        self._main_channel = Necrobot().main_channel
        self._notifications_channel = Necrobot().find_channel('bot_notifications')
        self._schedule_channel = Necrobot().find_channel('schedule')
        self._client = Necrobot().client

        await self.update_schedule_channel()

    async def refresh(self):
        self._notifications_channel = Necrobot().find_channel('bot_notifications')
        self._schedule_channel = Necrobot().find_channel('schedule')
        self._client = Necrobot().client
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
                match=ev.match, winner=ev.winner, winner_wins=ev.winner_wins, loser_wins=ev.loser_wins
            )
        elif ev.event_type == 'end_match_race':
            await VodRecorder().end_record(ev.match.racer_1.rtmp_name)
            await VodRecorder().end_record(ev.match.racer_2.rtmp_name)
        elif ev.event_type == 'match_alert':
            await self.match_alert(ev.match) if ev.final else self.cawmentator_alert(ev.match)
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
    async def get_gsheet(wks_id: str):
        return await sheetlib.get_sheet(
            gsheet_id=LeagueMgr().league.gsheet_id,
            wks_id=wks_id
        )

    async def cawmentator_alert(self, match: Match):
        """PM an alert to the match cawmentator, if any, that the match is soon to begin
        
        Parameters
        ----------
        match: Match
        """
        # PM a cawmentator alert
        cawmentator = await match.get_cawmentator()
        if cawmentator is None:
            return

        alert_format_str = 'Reminder: You\'re scheduled to cawmentate **{racer_1}** - **{racer_2}**, ' \
                           'which is scheduled to begin in {minutes} minutes.\n\n'
        alert_text = alert_format_str.format(
            racer_1=match.racer_1.display_name,
            racer_2=match.racer_2.display_name,
            minutes=(match.time_until_match.total_seconds() + 30) // 60
        )

        racer_1_stats = await statfn.get_league_stats(match.racer_1.user_id)
        racer_2_stats = await statfn.get_league_stats(match.racer_2.user_id)

        alert_text += await userutil.get_big_infotext(match.racer_1, racer_1_stats) + '\n'
        alert_text += await userutil.get_big_infotext(match.racer_2, racer_2_stats) + '\n'

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

        minutes_until_match = (match.time_until_match.total_seconds() + 30) // 60
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
        async for msg in Necrobot().client.logs_from(self._schedule_channel):
            if msg.author.id == Necrobot().client.user.id:
                the_msg = msg
                break

        if the_msg is None:
            await Necrobot().client.send_message(
                self._schedule_channel,
                infotext
            )
        else:
            await Necrobot().client.edit_message(
                message=the_msg,
                new_content=infotext
            )
