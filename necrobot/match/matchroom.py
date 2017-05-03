"""Room for scheduling and running a "match", a series of games between a pair of racers."""

import asyncio
import datetime
import discord
import pytz
import typing

from necrobot.botbase import server
from necrobot.util import console
from necrobot.util import ordinal
from necrobot.util import timestr

from necrobot.race import cmd_race
from necrobot.match import cmd_match
from necrobot.test import cmd_test

from necrobot.database import ratingsdb, matchdb, racedb
from necrobot.ladder import ratingutil
from necrobot.race import raceinfo

from necrobot.botbase.botchannel import BotChannel
from necrobot.config import Config
from necrobot.match.match import Match
from necrobot.match.matchracedata import MatchRaceData
from necrobot.necroevent.necroevent import NEDispatch
from necrobot.race.raceconfig import RaceConfig
from necrobot.race.race import Race, RaceEvent


class MatchRoom(BotChannel):
    def __init__(self, match_discord_channel: discord.Channel, match: Match):
        """BotChannel where a match is taking place.
        
        Parameters
        ----------
        match_discord_channel: discord.Channel
            The discord channel corresponding to this BotChannel.
        match: Match
            The Match object for the match.
        """
        BotChannel.__init__(self)
        self._channel = match_discord_channel   # type: discord.Channel
        self._match = match                     # type: Match

        self._current_race = None               # type: Race
        self._last_begun_race = None            # type: Race

        self._countdown_to_match_future = None  # type: asyncio.Future

        self._current_race_number = None        # type: typing.Optional[int]

        self._last_begun_race_number = None     # type: typing.Optional[int]
        self._current_race_contested = False    # type: bool

        self._match_race_data = None            # type: typing.Optional[MatchRaceData]

        self._prematch_channel_commands = [
            cmd_match.Confirm(self),
            cmd_match.GetMatchInfo(self),
            cmd_match.Suggest(self),
            cmd_match.Unconfirm(self),
            cmd_match.ForceBegin(self),
            cmd_match.ForceConfirm(self),
            cmd_match.ForceReschedule(self),
            cmd_match.Postpone(self),
            cmd_match.RebootRoom(self),
            cmd_match.SetMatchType(self),
            cmd_match.Update(self),

            cmd_test.TestMatch(self),
        ]

        self._during_match_channel_commands = [
            cmd_match.CancelRace(self),
            cmd_match.ChangeWinner(self),
            cmd_match.Contest(self),
            cmd_match.ForceNewRace(self),
            cmd_match.ForceRecordRace(self),
            cmd_match.GetMatchInfo(self),
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

            cmd_test.TestMatch(self),
        ]

        self._postmatch_channel_commands = [
            cmd_match.CancelRace(self),
            cmd_match.ChangeWinner(self),
            cmd_match.Contest(self),
            cmd_match.ForceNewRace(self),
            cmd_match.ForceRecordRace(self),
            cmd_match.GetMatchInfo(self),
            cmd_match.Postpone(self),
            cmd_match.RebootRoom(self),
            cmd_match.SetMatchType(self),
            cmd_match.Update(self),

            cmd_race.ChangeRules(self),

            cmd_test.TestMatch(self),
        ]

        self.channel_commands = self._prematch_channel_commands

# Properties
    @property
    def channel(self) -> discord.Channel:
        return self._channel

    @property
    def match(self) -> Match:
        return self._match

    @property
    def current_race(self) -> typing.Optional[Race]:
        """The "main" Race; the one that most commands should apply to. Not None if self.before_races is False."""
        return self._current_race

    @property
    def last_begun_race(self) -> typing.Optional[Race]:
        """The last race to begin (sent a RaceEvent.RACE_BEGIN to this room). Useful for allowing commands to apply
        to a finished race during the ready-up phase of the subsequent race.
        """
        return self._last_begun_race

    @property
    def played_all_races(self) -> bool:
        """True if the match is over."""
        if self._match_race_data is None:
            return False

        if self.match.is_best_of:
            return self._match_race_data.leader_wins > self.match.number_of_races // 2
        else:
            return self._match_race_data.num_finished >= self.match.number_of_races

    async def during_races(self) -> bool:
        """True if the match has started but not finished."""
        return self.current_race is not None and not self.played_all_races

    async def contest_last_begun_race(self) -> None:
        """Mark the last begun race as contested."""
        if self._last_begun_race is not None and not self._last_begun_race.final:
            self._current_race_contested = True
            return

        if self._last_begun_race_number == 0:
            return

        contest_race_number = self._last_begun_race_number

        await matchdb.set_match_race_contested(
            match=self.match,
            race_number=contest_race_number,
            contested=True
        )

    async def initialize(self) -> None:
        """Async initialization method"""
        if self._countdown_to_match_future is not None:
            self._countdown_to_match_future.cancel()
        self._countdown_to_match_future = asyncio.ensure_future(self._countdown_to_match_start(warn=True))
        self._match_race_data = await matchdb.get_match_race_data(self.match.match_id)
        self._current_race_number = self._match_race_data.num_finished + self._match_race_data.num_canceled
        self._last_begun_race_number = self._current_race_number
        self._set_channel_commands()

    async def send_channel_start_text(self) -> None:
        msg = '\n \N{BULLET} To suggest a time, use `.suggest`. (See `.help suggest` for more info.) Give the time ' \
              'in your own local timezone (which you\'ve registered using `.timezone`).\n' \
              '\N{BULLET} Confirm a suggested time with `.confirm`. You may remove a confirmation with ' \
              '`.unconfirm`.\n' \
              '\N{BULLET} To reschedule a time both racers have confirmed, both racers must call `.unconfirm`.\n' \
              '\N{BULLET} You may alert CoNDOR staff at any time by calling `.staff`.\n'

        if self.match.racer_1.timezone is not None and self.match.racer_2.timezone is not None:
            utcnow = pytz.utc.localize(datetime.datetime.utcnow())
            r1off = utcnow.astimezone(self.match.racer_1.timezone).utcoffset()
            r2off = utcnow.astimezone(self.match.racer_2.timezone).utcoffset()

            if r1off > r2off:
                ahead_racer_name = self.match.racer_1.display_name
                behind_racer_name = self.match.racer_2.display_name
                diff_str = timestr.timedelta_to_str(r1off - r2off)
                # noinspection PyUnresolvedReferences
                msg += '\N{BULLET} {0} is currently {1} ahead of {2}.'.format(
                    ahead_racer_name, diff_str, behind_racer_name
                )
            elif r1off < r2off:
                ahead_racer_name = self.match.racer_2.display_name
                behind_racer_name = self.match.racer_1.display_name
                diff_str = timestr.timedelta_to_str(r2off - r1off)
                # noinspection PyUnresolvedReferences
                msg += '\N{BULLET} {0} is currently {1} ahead of {2}.'.format(
                    ahead_racer_name, diff_str, behind_racer_name
                )
            else:
                # noinspection PyUnresolvedReferences
                msg += '\N{BULLET} The two racers in this match currently have the same UTC offset.'

        else:
            if self.match.racer_1.timezone is None and self.match.racer_2.timezone is not None:
                # noinspection PyUnresolvedReferences
                msg += '\N{BULLET} {0} has not registered a timezone. Please call `.timezone`.'.format(
                    self.match.racer_1.display_name
                )
            elif self.match.racer_1.timezone is not None and self.match.racer_2.timezone is None:
                # noinspection PyUnresolvedReferences
                msg += '\N{BULLET} {0} has not registered a timezone. Please call `.timezone`.'.format(
                    self.match.racer_2.display_name
                )
            else:
                # noinspection PyUnresolvedReferences
                msg += '\N{BULLET} {0} and {1} have not registered a timezone. Please call `.timezone`.'.format(
                    self.match.racer_1.display_name,
                    self.match.racer_2.display_name
                )

        await self.client.send_message(self.channel, msg)

    async def update(self) -> None:
        if self.match.is_scheduled and self.current_race is None:
            if self._countdown_to_match_future is not None:
                self._countdown_to_match_future.cancel()
            self._countdown_to_match_future = asyncio.ensure_future(self._countdown_to_match_start())
        elif not self.match.is_scheduled:
            if self._countdown_to_match_future is not None:
                self._countdown_to_match_future.cancel()
            self._current_race = None

        self._set_channel_commands()

        if self.played_all_races:
            self._end_match()

    async def change_race_info(self, command_args: list) -> None:
        """Change the RaceInfo for this room by parsing the input args"""
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

    async def process(self, race_event: RaceEvent) -> None:
        """Process a RaceEvent"""
        if race_event.event == RaceEvent.EventType.RACE_BEGIN:
            self._last_begun_race = self._current_race
            self._last_begun_race_number = self._current_race_number
        elif race_event.event == RaceEvent.EventType.RACE_BEGIN_COUNTDOWN:
            await NEDispatch().publish(event_type='begin_match_race', match=self.match)
        elif race_event.event == RaceEvent.EventType.RACE_END:
            await asyncio.sleep(1)  # Waiting for a short time feels good UI-wise
            await self.write('The race will end in {} seconds.'.format(self.current_race.race_config.finalize_time_sec))
        elif race_event.event == RaceEvent.EventType.RACE_FINALIZE:
            await NEDispatch().publish(event_type='end_match_race', match=self.match)

            race_winner = race_event.race.racers[0]
            race_loser = race_event.race.racers[1]
            auto_contest = (
                race_winner.is_finished
                and race_loser.is_finished
                and race_loser.time - race_winner.time <= Config.MATCH_AUTOCONTEST_IF_WITHIN_HUNDREDTHS
            )

            if auto_contest:
                self._current_race_contested = True
                await NEDispatch().publish(
                    'notify',
                    message='A race has been automatically contested in channel {0}, because the finish times were '
                            'close.'.format(self.channel.mention)
                )

            await self._record_race(race_event.race, self._race_winner(race_event.race))
            # await self._record_new_ratings(race_winner)

            # Write end-of-race message
            end_race_msg = 'The race has ended.'
            if auto_contest:
                if server.staff_role is not None:
                    end_race_msg += ' {0}:'.format(server.staff_role.mention)
                end_race_msg += ' This match has been automatically marked as contested because the finish times ' \
                                'were close.'
            await self.write(end_race_msg)

            # Begin a new race if appropriate, or end the match.
            if self.played_all_races:
                await self._end_match()
            else:
                await self._begin_new_race()
        elif race_event.event == RaceEvent.EventType.RACE_CANCEL:
            await self.write('The race has been canceled.')
            if not self.played_all_races:
                await self._begin_new_race()

    async def write(self, text: str) -> None:
        """Write text to the channel"""
        await self.client.send_message(self.channel, text)

    async def alert_racers(self) -> None:
        """Post an alert pinging both racers in the match"""
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
                alert_str[:-2], int(minutes_until_match))
            )

    async def force_new_race(self) -> None:
        """Begin a new race, canceling the old one if necessary"""
        if self.current_race is not None and not self.current_race.complete:
            await self.current_race.cancel()

        await self._begin_new_race()

    async def cancel_race(self, race_number: int) -> bool:
        """Mark a race as canceled
        
        Parameters
        ----------
        race_number: int
            The number of the race to cancel, counting only uncanceled races.
        """
        race_number = race_number - self._match_race_data.num_canceled
        success = await matchdb.cancel_race(self.match, race_number)
        if success:
            self._match_race_data.num_finished -= 1
            self._match_race_data.num_canceled += 1
        return success

    async def force_record_race(self, winner: int) -> None:
        """Record a "fake" race with the given winner"""
        await matchdb.record_match_race(
            match=self.match,
            winner=winner
        )
        self._update_race_data(race_winner=winner)

    async def _countdown_to_match_start(self, warn: bool = False) -> None:
        """Does things at certain times before the match
        
        Posts alerts to racers in this channel, and sends NecroEvents at alert times. Begins the match
        at the appropriate time. This is stored as a future in this object, and is meant to be canceled
        if this object closes.
        """
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
            if time_until_match > Config.MATCH_FIRST_WARNING:
                await asyncio.sleep((time_until_match - Config.MATCH_FIRST_WARNING).total_seconds())
                await self.alert_racers()
                await NEDispatch().publish('match_alert', match=self.match, final=False)

            # Wait until the final warning
            time_until_match = self.match.time_until_match
            if time_until_match > Config.MATCH_FINAL_WARNING:
                await asyncio.sleep((time_until_match - Config.MATCH_FINAL_WARNING).total_seconds())

            # At this time, we've either just passed the FINAL_MATCH_WARNING or the function was just called
            # (happens if the call comes sometime after the FINAL_MATCH_WARNING but before the match).
            await self.alert_racers()
            await NEDispatch().publish('match_alert', match=self.match, final=True)

            await asyncio.sleep(self.match.time_until_match.total_seconds())
            await self._begin_new_race()
        except asyncio.CancelledError:
            console.info('MatchRoom._countdown_to_match_start() was cancelled.')
            raise

    async def _begin_new_race(self):
        """Begin a new race"""
        # Shift to during-match commands
        self.channel_commands = self._during_match_channel_commands

        # Make the race
        match_race_data = await matchdb.get_match_race_data(self.match.match_id)
        self._current_race = Race(self, self.match.race_info,
                                  race_config=RaceConfig(finalize_time_sec=15, auto_forfeit=1))
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
        """End the match"""
        self._current_race = None
        self.channel_commands = self._postmatch_channel_commands

        # Send event
        if self._match_race_data.r1_wins > self._match_race_data.r2_wins:
            winner = self.match.racer_1.display_name
            winner_wins = self._match_race_data.r1_wins
            loser_wins = self._match_race_data.r2_wins
        elif self._match_race_data.r2_wins > self._match_race_data.r1_wins:
            winner = self.match.racer_2.display_name
            winner_wins = self._match_race_data.r2_wins
            loser_wins = self._match_race_data.r1_wins
        else:
            winner = '[Tied]'
            winner_wins = self._match_race_data.r1_wins
            loser_wins = self._match_race_data.r2_wins

        await NEDispatch().publish(
            'end_match',
            match=self.match,
            winner=winner,
            winner_wins=winner_wins,
            loser_wins=loser_wins,
            r1_wins=self._match_race_data.r1_wins,
            r2_wins=self._match_race_data.r2_wins
        )

        await self.write('Match complete.')

    async def _record_race(self, race: Race, race_winner: int) -> None:
        """Record the given race as part of this match"""
        await racedb.record_race(race)
        await matchdb.record_match_race(
            match=self.match,
            race_number=self._current_race_number,
            race_id=self.current_race.race_id,
            winner=race_winner,
            contested=self._current_race_contested,
            canceled=False
        )
        self._update_race_data(race_winner=race_winner)

    async def _record_new_ratings(self, race_winner: int) -> None:
        """Get new ratings for the racers in this match and record them"""
        racer_1 = self.match.racer_1
        racer_2 = self.match.racer_2

        rating_1 = await ratingsdb.get_rating(racer_1.discord_id)
        rating_2 = await ratingsdb.get_rating(racer_2.discord_id)

        new_ratings = ratingutil.get_new_ratings(rating_1=rating_1, rating_2=rating_2, winner=race_winner)

        await ratingsdb.set_rating(racer_1.discord_id, new_ratings[0])
        await ratingsdb.set_rating(racer_2.discord_id, new_ratings[1])

        # this isn't working
        # if Config.RATINGS_IN_NICKNAMES:
        #     for pair in [(racer_1, rating_1,), (racer_2, rating_2,)]:
        #         member = pair[0].member
        #         nick = '{0} ({1})'.format(pair[0].member.name, pair[1].displayed_rating)
        #         await self.client.change_nickname(member=member, nickname=nick)

    def _set_channel_commands(self) -> None:
        if self.current_race is None:
            if self.played_all_races:
                self.channel_commands = self._postmatch_channel_commands
            else:
                self.channel_commands = self._prematch_channel_commands
        else:
            self.channel_commands = self._during_match_channel_commands

    def _race_winner(self, race: Race) -> int:
        """Get the number of the race's winner (1 or 2, for match.racer_1 or match.racer_2)"""
        race_winner_id = int(race.winner.member.id)
        if race_winner_id == int(self.match.racer_1.member.id):
            return 1
        elif race_winner_id == int(self.match.racer_2.member.id):
            return 2
        else:
            return 0

    def _update_race_data(self, race_winner: int) -> None:
        """Update this object's MatchRaceData"""
        self._match_race_data.num_finished += 1
        if race_winner == 1:
            self._match_race_data.r1_wins += 1
        else:
            self._match_race_data.r2_wins += 1
