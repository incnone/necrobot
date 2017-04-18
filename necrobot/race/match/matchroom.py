# Room for scheduling and running a "match", a series of games between a pair of racers.

import asyncio
import datetime
import discord

from necrobot.botbase import cmd_admin
from necrobot.database import necrodb
from necrobot.race import cmd_race
from necrobot.race import raceinfo
from necrobot.race.match import cmd_match
from necrobot.util import console
from necrobot.util import ordinal

from necrobot.botbase.botchannel import BotChannel
from necrobot.race.match.match import Match
from necrobot.race.raceconfig import RaceConfig
from necrobot.race.race import Race
from necrobot.race.raceevent import RaceEvent


FIRST_MATCH_WARNING = datetime.timedelta(minutes=15)
FINAL_MATCH_WARNING = datetime.timedelta(minutes=5)


class MatchRoom(BotChannel):
    def __init__(self, match_discord_channel: discord.Channel, match: Match):
        BotChannel.__init__(self)
        self._channel = match_discord_channel   # The necrobot in which this match is taking place
        self._match = match                     # The match for this room

        self._current_race = None               # The current race
        self._last_begun_race = None            # The last race to begin

        self._countdown_to_match_future = None  # Future that waits until the match start, then begins match

        self._current_race_number = None
        self._current_race_contested = False

        self._prematch_command_types = [
            cmd_admin.Help(self),

            cmd_match.Confirm(self),
            cmd_match.MatchInfo(self),
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

            cmd_match.MatchInfo(self),
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

# Properties
    @property
    def channel(self) -> discord.Channel:
        return self._channel

    @property
    def match(self) -> Match:
        return self._match

    @property
    def current_race(self) -> Race:
        return self._current_race

    @property
    def last_begun_race(self) -> Race or None:
        return self._last_begun_race

    @property
    def played_all_races(self) -> bool:
        match_race_data = necrodb.get_match_race_data(self.match.match_id)
        if self.match.is_best_of:
            return match_race_data.leader_wins > self.match.number_of_races // 2
        else:
            return match_race_data.num_finished >= self.match.number_of_races

    @property
    def before_races(self) -> bool:
        return self.current_race is None and self.last_begun_race is None

# Public coroutine methods
    async def initialize(self):
        if self._countdown_to_match_future is not None:
            self._countdown_to_match_future.cancel()
        self._countdown_to_match_future = asyncio.ensure_future(self._countdown_to_match_start(warn=True))

    async def update(self):
        if self.match.is_scheduled and self.before_races:
            if self._countdown_to_match_future is not None:
                self._countdown_to_match_future.cancel()
            self._countdown_to_match_future = asyncio.ensure_future(self._countdown_to_match_start())

    # Change the RaceInfo for this room
    async def change_race_info(self, command_args: str):
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

    # Process a RaceEvent
    async def process(self, event: RaceEvent):
        if event == RaceEvent.RACE_BEGIN:
            self._last_begun_race = self._current_race
        elif event == RaceEvent.RACE_END:
            await asyncio.sleep(1)  # Waiting for a short time feels good UI-wise
            await self.write('The race will end in {} seconds.'.format(self.current_race.config.finalize_time_sec))
        elif event == RaceEvent.RACE_FINALIZE:
            await self._record_match_race()
            await self.write('The race has ended.'.format(self.current_race.config.finalize_time_sec))
            if self.played_all_races:
                await self._end_match()
            else:
                await self._begin_new_race()

    # Write to the channel
    async def write(self, text: str):
        await self.client.send_message(self.channel, text)

    # Post an alert pinging all racers in the match
    async def alert_racers(self):
        member_1 = self.match.racer_1.member
        member_2 = self.match.racer_2.member

        alert_str = ''
        if member_1 is not None:
            alert_str += member_1.mention + ', '
        if member_2 is not None:
            alert_str += member_2.mention + ', '

        if alert_str:
            minutes_until_match = int((self.match.time_until_match.total_seconds() + 30) // 60)
            await self.write('{0}: The match is scheduled to begin in {1} minutes.'.format(
                alert_str[:-2], minutes_until_match))

    # PM an alert to the match cawmentator, if any
    async def alert_cawmentator(self):
        pass  # TODO

    # Post a match alert in the main channel
    async def post_match_alert(self):
        pass  # TODO

# Private coroutine methods
    # Countdown to the start of the match, then begin
    async def _countdown_to_match_start(self, warn=False):
        try:
            if not self.match.is_scheduled:
                return

            time_until_match = self.match.time_until_match

            # Begin match now if appropriate
            if time_until_match < datetime.timedelta(seconds=0):
                if not self.played_all_races:
                    if warn:
                        await self.write(
                            'I believe that I was just restarted; an error may have occurred. I am '
                            'beginning a new race and attempting to pick up this match where we left '
                            'off. If this is an error, or if there are unrecorded races, please contact '
                            'an admin.')
                    await self._begin_new_race()
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
            await self._begin_new_race()
        except asyncio.CancelledError:
            console.info('MatchRoom._countdown_to_match_start() was cancelled.')
            raise

    # Begin a new race
    async def _begin_new_race(self):
        # Shift to during-match commands
        self.command_types = self._during_match_command_types

        # Make the race
        match_race_data = necrodb.get_match_race_data(self.match.match_id)
        self._current_race = Race(self, self.match.race_info,
                                  config=RaceConfig(finalize_time_sec=15, auto_forfeit=1))
        self._current_race_number = match_race_data.num_races + 1
        await self._current_race.initialize()

        # Enter the racers automatically
        for racer in self.match.racers:
            await self.current_race.enter_member(racer.member, mute=True)

        # Output text
        await self.write(
            'Please input the seed ({1}) and type `.ready` when you are ready for the {0} race. '
            'When both racers `.ready`, the race will begin.'.format(
                ordinal.num_to_text(match_race_data.num_finished + 1),
                self.current_race.race_info.seed))

        if self._countdown_to_match_future is not None:
            self._countdown_to_match_future.cancel()

    async def _end_match(self):
        await self.write('Match complete.')

    async def _record_match_race(self):
        race_winner_id = int(self.current_race.winner.member.id)
        if race_winner_id == int(self.match.racer_1.member.id):
            race_winner = 1
        elif race_winner_id == int(self.match.racer_2.member.id):
            race_winner = 2
        else:
            race_winner = 0

        necrodb.record_match_race(
            match=self.match,
            race_number=self._current_race_number,
            race_id=self.current_race.race_id,
            winner=race_winner,
            contested=self._current_race_contested,
            canceled=False
        )
