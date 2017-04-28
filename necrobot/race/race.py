# Class implementing a single race. The parent passed to the constructor should implement the methods:
#   async def write(str)
#   async def process(RaceEvent)

import asyncio
import datetime
import discord
import time
from enum import IntEnum, Enum

import necrobot.util.level
from necrobot.util import console, seedgen, racetime
from necrobot.util.ordinal import ordinal
# from necrobot.util import ratelimit

from necrobot.race.raceconfig import RaceConfig
from necrobot.race.raceinfo import RaceInfo
from necrobot.race.racer import Racer
from necrobot.config import Config

# CHECK_RATE_LIMITS = False


# RaceEvent ---------------------------------------------
class RaceEvent(object):
    class EventType(Enum):
        RACER_ENTER = 0
        RACER_UNENTER = 1
        RACER_READY = 2
        RACER_UNREADY = 3
        RACER_FINISH = 4
        RACER_UNFINISH = 5
        RACER_FORFEIT = 6
        RACER_UNFORFEIT = 7

        RACE_BEGIN_COUNTDOWN = 101
        RACE_CANCEL_COUNTDOWN = 102
        RACE_BEGIN = 103
        RACE_END = 104
        RACE_CANCEL_FINALIZE = 105
        RACE_FINALIZE = 106
        RACE_CANCEL = 107
        RACE_PAUSE = 108
        RACE_UNPAUSE = 109

        ADD_EXTRANEOUS = 201
        CHANGE_RULES = 202

    def __init__(self, race, event: EventType, **kwargs):
        self.race = race
        self.event = event
        self._kwargs = kwargs

    def __getattr__(self, item):
        return self._kwargs[item]


# RaceStatus enum ---------------------------------------------------------
class RaceStatus(IntEnum):
    """An Enum describing the current "phase" of the race.
    
    Values
    ------
        uninitialized  
            initialize() should be called on this object (not called in __init__ because coroutine).
        entry_open      
            The race is open to new entrants.
        counting_down
            The racebot is counting down to race start.
            If people .unready during this time, race reverts to the entry_open state.
        racing 
            The race has begun, and at least one player is still racing.
        race_completed
            All players have either finished or forfeited.
            If players .undone during this time, race reverts to the racing state.
        race_finalized
            All players have finished or forfeited, and the race results are marked as final and can be
            recorded. No further changes possible.
        canceled
            The race has been canceled. No further changes possible.    
    """

    uninitialized = 0
    entry_open = 1
    counting_down = 2
    racing = 3
    paused = 4
    completed = 5
    finalized = 6
    canceled = 7

    def __str__(self):
        status_strs = {
            RaceStatus.uninitialized: 'Not initialized.',
            RaceStatus.entry_open: 'Entry open!',
            RaceStatus.counting_down: 'Starting!',
            RaceStatus.racing: 'In progress!',
            RaceStatus.paused: 'Paused!',
            RaceStatus.completed: 'Complete.',
            RaceStatus.finalized: 'Results finalized.',
            RaceStatus.canceled: 'Race canceled.'
        }
        return status_strs[self]


# Race class --------------------------------------------------------------
class Race(object):
    # NB: Call the coroutine initialize() to set up the room
    def __init__(self, parent, race_info: RaceInfo, race_config: RaceConfig = RaceConfig()):
        self.race_id = None                       # After recording, the ID of the race in the DB
        self.parent = parent                      # The parent managing this race. Must implement write() and process().
        self.race_info = RaceInfo.copy(race_info)
        self.racers = []                          # A list of Racer

        self._status = RaceStatus.uninitialized   # The status of this race
        self._config = race_config                # The RaceConfig to use (determines some race behavior)

        self._countdown = int(0)                  # The current countdown
        self._start_datetime = None               # UTC time for the beginning of the race
        self._adj_start_time = float(0)           # System clock time for the beginning of the race (modified by pause)
        self._last_pause_time = float(0)          # System clock time for last time we called pause()

        self._last_no_entrants_time = None        # System clock time for the last time the race had zero entrants

        self._delay_record = False                # If true, delay an extra config.FINALIZE_TIME_SEC before recording
        self._countdown_future = None             # The Future object for the race countdown
        self._finalize_future = None              # The Future object for the finalization countdown

# Race data
    # Returns the status string
    @property
    def status_str(self) -> str:
        return str(self._status)

    # Returns time elapsed in the race in ms
    @property
    def current_time(self) -> int or None:
        if self._status == RaceStatus.paused:
            return int(100 * (self._last_pause_time - self._adj_start_time))
        elif self._status == RaceStatus.racing or self._status == RaceStatus.completed:
            return int(100 * (time.monotonic() - self._adj_start_time))
        else:
            return None

    # Returns the current time elapsed as a string "[m]m:ss.hh"
    @property
    def current_time_str(self) -> str:
        current_time_ = self.current_time
        if current_time_ is not None:
            return racetime.to_str(current_time_)
        else:
            return ''

    # Returns the UTC time for the beginning of the race
    @property
    def start_datetime(self) -> datetime.datetime:
        return self._start_datetime

    # True if the race has not started
    @property
    def before_race(self) -> bool:
        return self._status < RaceStatus.racing

    # True if the race is currently running
    @property
    def during_race(self) -> bool:
        return self._status == RaceStatus.racing or self._status == RaceStatus.paused

    # True if the race is finalized or canceled
    @property
    def complete(self) -> bool:
        return self._status >= RaceStatus.completed

    # True if racers can enter the race
    @property
    def entry_open(self) -> bool:
        return self._status == RaceStatus.entry_open

    # True if the race can no longer be modified (finalized or canceled)
    @property
    def final(self) -> bool:
        return self._status >= RaceStatus.finalized

    # True if we've passed the "no entrants" warning
    @property
    def passed_no_entrants_warning_time(self) -> bool:
        time_since = datetime.timedelta(seconds=(time.monotonic() - self._last_no_entrants_time))
        return self._status != RaceStatus.uninitialized and time_since > Config.NO_ENTRANTS_CLEANUP_WARNING

    # True if we've passed the "no entrants" clear time
    @property
    def passed_no_entrants_cleanup_time(self) -> bool:
        time_since = datetime.timedelta(seconds=(time.monotonic() - self._last_no_entrants_time))
        return self._status != RaceStatus.uninitialized and time_since > Config.NO_ENTRANTS_CLEANUP

    # True if the race has any entrants
    @property
    def any_entrants(self) -> bool:
        return bool(self.racers)

    # True if the race is paused
    @property
    def paused(self) -> bool:
        return self._status == RaceStatus.paused

    @property
    def race_config(self) -> RaceConfig:
        return self._config

# Racer data
    # Returns true if all racers are ready and there's enough racers
    @property
    def all_racers_ready(self) -> bool:
        return self.num_not_ready == 0 and (self.race_info.can_be_solo or len(self.racers) > 1)

    # Returns the number of racers not in the 'ready' state
    @property
    def num_not_ready(self) -> int:
        num = 0
        for racer in self.racers:
            if not racer.is_ready:
                num += 1
        return num

    # Return the number of racers in the 'finished' state
    @property
    def num_finished(self) -> int:
        num = 0
        for racer in self.racers:
            if racer.is_finished:
                num += 1
        return num

    # Returns a list of racers and their statuses.
    @property
    def leaderboard_text(self) -> str:
        return self._leaderboard_text(False)

    def _leaderboard_text(self, shortened) -> str:
        char_limit = int(1900)      # The character limit on discord messages

        racer_list = []
        max_name_len = 0
        max_time = 0
        for racer in self.racers:
            max_name_len = max(max_name_len, len(racer.name))
            racer_list.append(racer)
            if racer.is_finished:
                max_time = max(racer.time, max_time)
        max_time += 1

        # Sort racers: (1) Finished racers, by time; (2) Forfeit racers; (3) Racers still racing
        racer_list.sort(key=lambda r: r.time if r.is_finished else (max_time if r.is_forfeit else max_time+1))

        text = ''
        rank = int(0)
        for racer in racer_list:
            rank += 1
            rank_str = '{0: >4} '.format(str(rank) + '.' if racer.is_finished else ' ')
            stat_str = racer.short_status_str if shortened else racer.status_str
            text += (rank_str + racer.name + (' ' * (max_name_len - len(racer.name))) + ' --- ' + stat_str + '\n')

        if len(text) > char_limit and not shortened:
            return self._leaderboard_text(shortened=True)
        else:
            return text

    @property
    def winner(self) -> int or None:
        if not self._status == RaceStatus.finalized or not self.racers:
            return None
        lead_racer = self.racers[0]
        return lead_racer if lead_racer.is_finished else None

    # True if the given discord.User is entered in the race
    def has_racer(self, racer_usr: discord.User) -> bool:
        for racer in self.racers:
            if int(racer.member.id) == int(racer_usr.id):
                return True
        return False

    # Returns the given discord.User as a Racer, if possible
    def get_racer(self, racer_usr: discord.User) -> Racer:
        for racer in self.racers:
            if int(racer.member.id) == int(racer_usr.id):
                return racer

# Public methods (all coroutines)
    # Sets up the leaderboard, etc., for the race
    async def initialize(self):
        if self._status != RaceStatus.uninitialized:
            return

        self._status = RaceStatus.entry_open
        self._last_no_entrants_time = time.monotonic()

    # Begins the race if ready. (Writes a message if all racers are ready but an admin is not.)
    # Returns true on success
    async def begin_if_ready(self):
        if self.all_racers_ready:
            await self.begin_race_countdown()
            return True

    # Begin the race countdown and transition race state from 'entry_open' to 'counting_down'
    async def begin_race_countdown(self):
        if self._status == RaceStatus.entry_open:
            self._status = RaceStatus.counting_down
            self._countdown_future = asyncio.ensure_future(self._race_countdown())
            await self._process(RaceEvent.EventType.RACE_BEGIN_COUNTDOWN)

    # Pause the race timer.
    async def pause(self, mute=False):
        if self._status == RaceStatus.racing:
            self._status = RaceStatus.paused
            self._last_pause_time = time.monotonic()
            mention_str = ''
            for racer in self.racers:
                mention_str += '{}, '.format(racer.member.mention)
            mention_str = mention_str[:-2]

            await self._write(mute=mute, text='Race paused. (Alerting {0}.)'.format(mention_str))
            await self._process(RaceEvent.EventType.RACE_PAUSE)

    # Unpause the race timer.
    async def unpause(self, mute=False):
        if self.paused:
            await self._unpause_countdown(mute=mute)

    # Enters the given discord Member in the race
    async def enter_member(self, racer_member: discord.Member, mute=False):
        if self.has_racer(racer_member):
            await self._write(mute=mute, text='{0} is already entered.'.format(racer_member.mention))
            return

        if not self.before_race:
            await self._write(
                mute=mute,
                text='{0}: Cannot enter; the race has already started.'.format(racer_member.mention))
            return

        if self._status == RaceStatus.counting_down:
            await self._cancel_countdown()

        await self._do_enter_racer(racer_member)
        await self._write(
            mute=mute,
            text='{0} has entered the race. {1} entrants.'.format(racer_member.mention, len(self.racers)))
        await self._process(RaceEvent.EventType.RACER_ENTER, racer_member=racer_member)

    # Unenters the given discord Member in the race
    async def unenter_member(self, racer_member: discord.Member, mute=False):
        if not self.before_race:
            await self.forfeit_member(racer_member)
            return

        if self.has_racer(racer_member):
            self.racers = [r for r in self.racers if int(r.member.id) != int(racer_member.id)]
            if not self.racers:
                self._last_no_entrants_time = time.monotonic()
            if (len(self.racers) < 2 and not self.race_info.can_be_solo) or len(self.racers) < 1:
                await self._cancel_countdown()
            await self._write(mute=mute, text='{0} is no longer entered.'.format(racer_member.mention))
            await self.begin_if_ready()
            await self._process(RaceEvent.EventType.RACER_UNENTER, racer_member=racer_member)
        else:
            await self._write(mute=mute, text='{0} is not entered.'.format(racer_member.mention))

    # Enters the racer if not entered, and puts that racer in the 'ready' state
    async def enter_and_ready_member(self, racer_member: discord.Member, mute=False):
        already_entered = self.has_racer(racer_member)

        if not already_entered and not self.before_race:
            await self._write(mute=mute, text='{0}: The race has already started!'.format(racer_member.mention))
            return

        if not already_entered:
            await self._do_enter_racer(racer_member)

        racer = self.get_racer(racer_member)
        if racer is None:
            await self._write(mute=mute, text='Unexpected error.')
            console.warning("Unexpected error in race.race.Race.enter_and_ready_member: "
                            "Couldn't find a Racer for the discord Member {0}.".format(racer_member.name))
            return

        if racer.is_ready:
            await self._write(mute=mute, text='{0} is already ready!'.format(racer_member.mention))
            return

        racer.ready()
        if self._status == RaceStatus.counting_down:
            await self._cancel_countdown()

        if len(self.racers) == 1 and not self.race_info.can_be_solo:
            await self._write(mute=mute, text='Waiting on at least one other person to join the race.')
        elif not already_entered:
            await self._write(
                mute=mute,
                text='{0} has entered and is ready! {1} remaining.'.format(racer_member.mention, self.num_not_ready))
        else:
            await self._write(
                mute=mute,
                text='{0} is ready! {1} remaining.'.format(racer_member.mention, self.num_not_ready))

        await self.begin_if_ready()
        if not already_entered:
            await self._process(RaceEvent.EventType.RACER_ENTER, racer_member=racer_member)
        await self._process(RaceEvent.EventType.RACER_READY, racer_member=racer_member)

    # Attempt to put the given Racer in the 'unready' state if they were ready
    async def unready_member(self, racer_member: discord.Member, mute=False):
        if not self.before_race:
            return

        racer = self.get_racer(racer_member)
        if racer is None:
            await self._write(
                mute=mute,
                text='{0}: Warning: You have not yet entered the race.'.format(racer_member.mention))
            return

        # See if we can cancel a countdown. If cancel_countdown() returns False,
        # then there is a countdown and we failed to cancel it, so racer cannot be made unready.
        success = await self._cancel_countdown()

        if success and racer.unready():
            await self._write(mute=mute, text='{0} is no longer ready.'.format(racer_member.mention))
            await self._process(RaceEvent.EventType.RACER_UNREADY, racer_member=racer_member)
        else:
            await self._write(mute=mute, text="Can't unready!")

    # Puts the given Racer in the 'finished' state and gets their time
    async def finish_member(self, racer_member: discord.Member, mute=False):
        if not (self._status == RaceStatus.racing or self._status == RaceStatus.completed):
            return

        racer = self.get_racer(racer_member)
        if racer is None:
            return

        if racer.finish(self.current_time):
            await self._write(
                mute=mute,
                text='{0} has finished in {1} place with a time of {2}.'.format(
                    racer_member.mention,
                    ordinal(self.num_finished),
                    racer.time_str))
            if self._status == RaceStatus.racing:
                await self._check_for_race_end()
            await self._process(RaceEvent.EventType.RACER_FINISH, racer_member=racer_member)

    # Attempt to put the given Racer in the 'racing' state if they were finished
    async def unfinish_member(self, racer_member: discord.Member, mute=False):
        if self.before_race or self.final:
            return

        racer = self.get_racer(racer_member)
        if racer is None:
            return

        if not racer.is_finished:
            await self._write(mute=mute, text='{0} is still racing!'.format(racer_member.mention))

        # See if we can cancel a (possible) finalization. If cancel_finalization() returns False,
        # then there is a finalization and we failed to cancel it, so racer cannot be made unready.
        success = await self._cancel_finalization()
        if success and racer.unfinish():
            await self._write(mute=mute, text='{0} continues to race!'.format(racer_member.mention))
            await self._process(RaceEvent.EventType.RACER_UNFINISH, racer_member=racer_member)

    async def forfeit_racer(self, racer: Racer, mute=False):
        if self.before_race or self.final:
            return

        await self._do_forfeit_racer(racer)
        await self._write(mute=mute, text='{0} has forfeit the race.'.format(racer.member.mention))

    # Puts the given Racer in the 'forfeit' state
    async def forfeit_member(self, racer_member: discord.Member, mute=False):
        racer = self.get_racer(racer_member)
        if racer is not None:
            await self.forfeit_racer(racer, mute)
            await self._process(RaceEvent.EventType.RACER_FORFEIT, racer_member=racer_member)

    # Attempt to put the given Racer in the 'racing' state if they had forfeit
    async def unforfeit_member(self, racer_member: discord.Member, mute=False):
        if self.before_race or self.final:
            return False

        racer = self.get_racer(racer_member)
        if racer is None:
            return

        if not racer.is_forfeit:
            return

        # See if we can cancel a (possible) finalization. If cancel_finalization() returns False,
        # then there is a finalization and we failed to cancel it, so racer cannot be made unready.
        success = await self._cancel_finalization()
        if success and racer.unforfeit():
            await self._write(
                mute=mute,
                text='{0} is no longer forfeit and continues to race!'.format(racer_member.mention))
            await self._process(RaceEvent.EventType.RACER_UNFORFEIT, racer_member=racer_member)

    # Forfeits all racers that have not yet finished
    async def forfeit_all_remaining(self, mute=False):
        if not self.before_race:
            forfeit_any = False
            for racer in self.racers:
                if racer.is_racing:
                    forfeit_any = True
                    await self._do_forfeit_racer(racer)
            if forfeit_any:
                await self._write(mute=mute, text='All remaining racers forfeit.')

    # Adds the given string as a comment
    async def add_comment_for_member(self, racer_member: discord.Member, comment_str: str):
        if self.before_race or self.final:
            return

        racer = self.get_racer(racer_member)
        if racer is None:
            return

        racer.add_comment(comment_str[:255])
        await self._process(RaceEvent.EventType.ADD_EXTRANEOUS)

    # Adds a death for the given member at the given level and causes them to forfeit
    async def set_death_for_member(self, racer_member: discord.Member, level: int, mute=False):
        if self.before_race or self.final:
            return

        racer = self.get_racer(racer_member)
        if racer is None:
            return

        await self._do_forfeit_racer(racer)
        await self._write(mute=mute, text='{0} has forfeit the race.'.format(racer_member.mention))
        if not level == necrobot.util.level.LEVEL_NOS:
            racer.level = level
        await self._process(RaceEvent.EventType.RACER_FORFEIT, racer_member=racer_member)

    # Adds an in-game time for the given member
    async def set_igt_for_member(self, racer_member: discord.Member, igt: int):
        if self.before_race or self.final:
            return

        racer = self.get_racer(racer_member)
        if racer is None:
            return

        if igt != -1 and racer.is_done_racing:
            racer.igt = int(igt)
            await self._process(RaceEvent.EventType.ADD_EXTRANEOUS)

    # Kicks the specified racers from the race (they can re-enter)
    async def kick_racers(self, names_to_kick: list, mute=False):
        for racer in self.racers:
            if racer.name.lower() in names_to_kick:
                await self.unenter_member(racer.member, mute=mute)

    # Cancel the race.
    async def cancel(self):
        self._status = RaceStatus.canceled
        await self._cancel_countdown()
        await self._cancel_finalization()
        await self._process(RaceEvent.EventType.RACE_CANCEL)

    # Reseed the race
    async def reseed(self, mute=False):
        if not self.race_info.seeded:
            await self._write(mute=mute, text='This is not a seeded race. Use `.changerulse` to change this.')

        elif self.race_info.seed_fixed:
            await self._write(
                mute=mute,
                text='The seed for this race was fixed by its rules. Use `.changerulse` to change this.')
            return

        else:
            self.race_info.seed = seedgen.get_new_seed()
            await self._write(mute=mute, text='Changed seed to {0}.'.format(self.race_info.seed))
            await self._process(RaceEvent.EventType.CHANGE_RULES)

# Private methods
    # Sort racer list
    def _sort_racers(self):
        max_time = 0
        for racer in self.racers:
            if racer.is_finished:
                max_time = max(racer.time, max_time)
        max_time += 1

        self.racers.sort(key=lambda r: r.time if r.is_finished else max_time)

    # Process an event
    async def _process(self, event_type: RaceEvent.EventType, **kwargs):
        await self.parent.process(RaceEvent(self, event_type, **kwargs))

    # Actually enter the racer
    async def _do_enter_racer(self, racer_member):
        racer = Racer(racer_member)
        await racer.initialize()
        if racer in self.racers:
            return
        self.racers.append(racer)

    # Begins the race. Called by the countdown.
    async def _begin_race(self, mute=False):
        for racer in self.racers:
            if not racer.begin_race():
                console.warning("{} isn't ready while calling race._begin_race -- unexpected error.".format(
                    racer.name))

        self._status = RaceStatus.racing
        self._adj_start_time = time.monotonic()
        self._start_datetime = datetime.datetime.utcnow()
        await self._write(mute=mute, text='GO!')
        await self._process(RaceEvent.EventType.RACE_BEGIN)

    # Checks to see if all racers have either finished or forfeited. If so, ends the race.
    # Return True if race was ended.
    async def _check_for_race_end(self):
        num_still_racing = 0
        for racer in self.racers:
            if not racer.is_done_racing:
                num_still_racing += 1

        if num_still_racing <= self._config.auto_forfeit:
            await self.forfeit_all_remaining(mute=True)
            await self._end_race()

    # Ends the race, and begins a countdown until the results are 'finalized'
    async def _end_race(self):
        if self._status == RaceStatus.racing:
            self._status = RaceStatus.completed
            self._finalize_future = asyncio.ensure_future(self._finalization_countdown())
            await self._process(RaceEvent.EventType.RACE_END)

    # Countdown coroutine to be wrapped in self._countdown_future.
    # Warning: Do not call this -- use begin_countdown instead.
    async def _race_countdown(self, mute=False):
        await self._do_countdown(
            length=self._config.countdown_length,
            incremental_start=self._config.incremental_countdown_start,
            mute=mute
        )

        await self._begin_race()

    async def _do_countdown(self, length: int, incremental_start: int = None, mute=False):
        fudge = 0.6

        countdown_systemtime_begin = time.monotonic()
        countdown_timer = length

        if incremental_start is not None:
            await self._write(mute=mute, text='The race will begin in {0} seconds.'.format(countdown_timer))
        while countdown_timer > 0:
            sleep_time = float(countdown_systemtime_begin + length - countdown_timer + 1 - time.monotonic())

            if incremental_start is None or countdown_timer <= incremental_start:
                await self._write(mute=mute, text='{}'.format(countdown_timer))

            if sleep_time < fudge:
                countdown_systemtime_begin += fudge - sleep_time
                sleep_time = fudge

            # print('Countdown cycle: Timer = {0}, Sleep Time = {1}'.format(countdown_timer, sleep_time))

            if sleep_time > 0:
                await asyncio.sleep(sleep_time)         # sleep until the next tick
            countdown_timer -= 1

    # Countdown for an unpause
    async def _unpause_countdown(self, mute=False):
        await self._do_countdown(
            length=self._config.unpause_countdown_length,
            mute=mute
        )

        await self._do_unpause_race()

    # Actually unpause the race
    async def _do_unpause_race(self, mute=False):
        if self._status == RaceStatus.paused:
            await self._write(mute=mute, text='GO!')
            self._status = RaceStatus.racing
            self._adj_start_time += time.monotonic() - self._last_pause_time
            await self._process(RaceEvent.EventType.RACE_UNPAUSE)
            return True
        return False

    # Countdown coroutine to be wrapped in self._finalize_future.
    # Warning: Do not call this -- use end_race instead.
    async def _finalization_countdown(self):
        self.delay_record = True
        while self.delay_record:
            self.delay_record = False
            await asyncio.sleep(self._config.finalize_time_sec)

        # Perform the finalization and record the race. At this point, the finalization cannot be canceled.
        self._status = RaceStatus.finalized
        await self.forfeit_all_remaining(mute=True)
        self._sort_racers()
        await self._process(RaceEvent.EventType.RACE_FINALIZE)

    # Attempt to cancel the race countdown -- transition race state from 'counting_down' to 'entry_open'
    # Returns False only if there IS a countdown, AND we failed to cancel it
    async def _cancel_countdown(self, mute=False):
        if self._status == RaceStatus.counting_down:
            if self._countdown_future:
                if self._countdown_future.cancel():
                    self._countdown_future = None
                    self._status = RaceStatus.entry_open
                    await self._process(RaceEvent.EventType.RACE_CANCEL_COUNTDOWN)
                    await self._write(mute=mute, text='Countdown canceled.')
                    return True
                else:
                    return False
        return True

    # Attempt to cancel finalization and restart race -- transition race state from 'completed' to 'racing'
    # Returns False only if race IS completed, AND we failed to restart it
    async def _cancel_finalization(self, mute=False):
        if self._status == RaceStatus.completed:
            if self._finalize_future:
                if self._finalize_future.cancel():
                    self._finalize_future = None
                    self._status = RaceStatus.racing
                    await self._process(RaceEvent.EventType.RACE_CANCEL_FINALIZE)
                    await self._write(mute=mute, text='Race end canceled -- unfinished racers may continue!')
                    return True
                else:
                    return False
        return True

    # Causes the racer to forfeit
    async def _do_forfeit_racer(self, racer: Racer):
        if racer.forfeit(self.current_time):
            await self._check_for_race_end()

    # Write text
    async def _write(self, text: str, mute=False):
        if not mute:
            await self.parent.write(text)
