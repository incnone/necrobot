# Room for scheduling and running a "match", a series of games between a common pool of racers.

import asyncio
import datetime

from necrobot.botbase import cmd_admin
from necrobot.race import cmd_race
from necrobot.race.match import cmd_match
from necrobot.race import raceinfo

from necrobot.botbase.botchannel import BotChannel
from necrobot.race.race import Race


FIRST_MATCH_WARNING = datetime.timedelta(minutes=15)
FINAL_MATCH_WARNING = datetime.timedelta(minutes=5)


class MatchRoom(BotChannel):
    def __init__(self, match_discord_channel, match):
        BotChannel.__init__(self)
        self._channel = match_discord_channel   # The necrobot in which this match is taking place
        self._match = match                     # The match for this room

        self._current_race = None               # The current race
        self._last_race = None                  # The last race to finish

        self._countdown_to_match_future = None  # Future that waits until the match start, then begins match

        self._prematch_command_types = [
            cmd_admin.Help(self),

            cmd_match.Confirm(self),
            cmd_match.Suggest(self),
            cmd_match.Unconfirm(self),
            cmd_match.ForceBegin(self),
            cmd_match.ForceConfirm(self),
            cmd_match.ForceReschedule(self),
            cmd_match.Postpone(self),
            cmd_match.RebootRoom(self),
            cmd_match.SetMatchType(self),
            cmd_match.Update(self),
        ]

        self._during_match_command_types = [
            cmd_admin.Help(self),

            cmd_match.CancelRace(self),
            cmd_match.ChangeWinner(self),
            cmd_match.ForceNewRace(self),
            cmd_match.ForceRecordRace(self),
            cmd_match.Postpone(self),
            cmd_match.RebootRoom(self),
            cmd_match.SetMatchType(self),
            cmd_match.Update(self),

            cmd_race.Ready(self),
            cmd_race.Unready(self),
            cmd_race.Done(self),
            cmd_race.Undone(self),
            cmd_race.Time(self),

            cmd_race.Pause(self),
            cmd_race.Unpause(self),
            cmd_race.Reseed(self),
            cmd_race.ChangeRules(self),
            cmd_race.ForceForfeit(self),
            cmd_race.ForceForfeitAll(self),
        ]

        self.command_types = self._prematch_command_types

    @property
    def channel(self):
        return self._channel

    @property
    def match(self):
        return self._match

    @property
    def current_race(self) -> Race:
        return self._current_race

    @property
    def last_begun_race(self) -> Race:
        return self._last_race

    @property
    def played_all_races(self) -> bool:
        return False  # TODO

    async def initialize(self):
        pass

    async def update(self):
        if self.match.is_scheduled:
            pass

    # Change the RaceInfo for this room
    async def change_race_info(self, command_args):
        new_race_info = raceinfo.parse_args_modify(
            command_args,
            raceinfo.RaceInfo.copy(self.match.race_info)
        )
        if new_race_info:
            self.match.set_race_info(new_race_info)
            if self.current_race.before_race:
                self.current_race.race_info = raceinfo.RaceInfo.copy(self.match.race_info)
            await self.write('Changed rules for the next race.')
            await self.update()

    # Write to the channel
    async def write(self, text):
        await self.client.send_message(self.channel, text)

    # Countdown to the start of the match, then begin
    async def countdown_to_match_start(self):
        if not self.match.is_scheduled:
            return

        time_until_match = self.match.time_until_match

        # Begin match now if appropriate
        if time_until_match < datetime.timedelta(seconds=0):
            if not self.played_all_races:
                await self.begin_new_race()
                return

        # Wait until the first warning
        if time_until_match > FIRST_MATCH_WARNING:
            await asyncio.sleep((time_until_match - FIRST_MATCH_WARNING).total_seconds())
            await self.alert_racers()
            await self.alert_cawmentator()

        # Wait until the final warning
        time_until_match = self.match.time_until_match
        if time_until_match > FINAL_MATCH_WARNING:
            await asyncio.sleep((time_until_match - FINAL_MATCH_WARNING).total_seconds())

        # At this time, we've either just passed the FINAL_MATCH_WARNING or the function was just called
        # (happens if the call comes sometime after the FINAL_MATCH_WARNING but before the match).
        await self.alert_racers()
        await self.post_match_alert()

        await asyncio.sleep(self.match.time_until_match.total_seconds())
        await self.begin_new_race()

    # Begin a new race
    async def begin_new_race(self):
        if self._countdown_to_match_future is not None:
            self._countdown_to_match_future.cancel()
        # TODO

    # Post an alert pinging all racers in the match
    async def alert_racers(self):
        member_1 = self.match.racer_1.member
        member_2 = self.match.racer_2.member

        alert_str = ''
        if member_1 is not None:
            alert_str += member_1.mention + ', '
        if member_2 is not None:
            alert_str += member_2.mention + ', '

        minutes_until_match = int((self.match.time_until_match.total_seconds() + 30) // 60)
        if alert_str:
            await self.write('{0}: The match is scheduled to begin in {1} minutes.'.format(
                alert_str[:-2], minutes_until_match))

    # PM an alert to the match cawmentator, if any
    async def alert_cawmentator(self):
        pass  # TODO

    # Post a match alert in the main channel
    async def post_match_alert(self):
        pass  # TODO