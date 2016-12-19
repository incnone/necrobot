import asyncio
import datetime
import time
from enum import IntEnum

from . import racetime
from .raceinfo import RaceInfo
from .racer import Racer
from ..necrodb import NecroDB
from ..util.config import Config
from ..util import console
from ..util.ordinal import ordinal


# RaceStatus enum ---------------------------------------------------------
class RaceStatus(IntEnum):
    uninitialized = 0
    entry_open = 1
    counting_down = 2
    racing = 3
    paused = 4
    completed = 5
    finalized = 6
    cancelled = 7

StatusStrs = {RaceStatus.uninitialized: 'Not initialized.',
              RaceStatus.entry_open: 'Entry open!',
              RaceStatus.counting_down: 'Starting!',
              RaceStatus.racing: 'In progrss!',
              RaceStatus.paused: 'Paused!',
              RaceStatus.completed: 'Complete.',
              RaceStatus.finalized: 'Results finalized.',
              RaceStatus.cancelled: 'Race cancelled.'}

#    uninitialized   --  initialize() should be called on this object (not called in __init__ because coroutine)
#    entry_open      --  the race is open to new entrants
#    counting_down   --  the racebot is counting down to race start.
#                        if people .unready during this time, race reverts to the entry_open state
#    racing          --  the race has begun, and at least one player is still racing
#    race_completed  --  all players have either finished or forfeited.
#                        if players .undone during this time, race reverts to the racing state
#    race_finalized  --  all players have finished or forfeited, and the race results are marked as final and can be
#                        recorded. no further changes possible.
#    cancelled       --  the race has been cancelled. no further changes possible.


# Race class --------------------------------------------------------------
class Race(object):
    # NB: Call the coroutine initialize() to set up the room
    def __init__(self, race_room):
        self.room = race_room                     # The RaceRoom object managing this race
        self.race_info = RaceInfo.copy(race_room.race_info)
        self.racers = []                          # A list of Racer

        self._status = RaceStatus.uninitialized   # The status of this race

        self._countdown = int(0)                  # The current countdown
        self._start_datetime = None               # UTC time for the beginning of the race
        self._adj_start_time = float(0)           # System clock time for the beginning of the race (modified by pause)
        self._last_pause_time = float(0)          # System clock time for last time we called pause()

        self._last_no_entrants_time = None        # System clock time for the last time the race had zero entrants

        self._delay_record = False                # If true, delay an extra Config.FINALIZE_TIME_SEC before recording
        self._countdown_future = None             # The Future object for the race countdown
        self._finalize_future = None              # The Future object for the finalization countdown

# Race data
    # Returns time elapsed in the race in ms
    @property
    def current_time(self):
        if self._status == RaceStatus.paused:
            return int(100 * (self._last_pause_time - self._adj_start_time))
        elif self._status == RaceStatus.racing:
            return int(100 * (time.monotonic() - self._adj_start_time))
        else:
            return None

    # Returns the current time elapsed as a string "[m]m:ss.hh"
    @property
    def current_time_str(self):
        current_time_ = self.current_time
        if current_time_ is not None:
            return racetime.to_str(current_time_)
        else:
            return ''

    # Returns the UTC time for the beginning of the race
    @property
    def start_datetime(self):
        return self._start_datetime

    # True if the race has not started
    @property
    def before_race(self):
        return self._status < RaceStatus.racing

    # True if the race is currently running
    @property
    def during_race(self):
        return self._status == RaceStatus.racing or self._status == RaceStatus.paused

    # True if the race is finalized or cancelled
    @property
    def complete(self):
        return self._status >= RaceStatus.completed

    # True if racers can enter the race
    @property
    def entry_open(self):
        return self._status == RaceStatus.entry_open

    # True if the race can no longer be modified (finalized or cancelled)
    @property
    def final(self):
        return self._status >= RaceStatus.finalized

    # True if we've passed the "no entrants" warning
    @property
    def passed_no_entrants_warning_time(self):
        return self._status != RaceStatus.uninitialized \
               and time.monotonic() - self._last_no_entrants_time > Config.NO_ENTRANTS_CLEANUP_WARNING_SEC

    # True if we've passed the "no entrants" clear time
    @property
    def passed_no_entrants_cleanup_time(self):
        return self._status != RaceStatus.uninitialized \
               and time.monotonic() - self._last_no_entrants_time > Config.NO_ENTRANTS_CLEANUP_SEC

    # True if the race has any entrants
    @property
    def any_entrants(self):
        return bool(self.racers)

    # True if the race is paused
    @property
    def paused(self):
        return self._status == RaceStatus.paused

# Racer data
    # Returns true if all racers are ready and there's enough racers
    @property
    def all_racers_ready(self):
        return self.num_not_ready == 0 and (not Config.REQUIRE_AT_LEAST_TWO_FOR_RACE or len(self.racers) > 1)

    # Returns the number of racers not in the 'ready' state
    @property
    def num_not_ready(self):
        num = 0
        for racer in self.racers:
            if not racer.is_ready:
                num += 1
        return num

    # Return the number of racers in the 'finished' state
    @property
    def num_finished(self):
        num = 0
        for racer in self.racers:
            if racer.is_finished:
                num += 1
        return num

    # True if the given discord.User is entered in the race
    def has_racer(self, racer_usr):
        for racer in self.racers:
            if int(racer.member.id) == int(racer_usr.id):
                return True
        return False

    # Returns the given discord.User as a Racer, if possible
    def get_racer(self, racer_usr):
        for racer in self.racers:
            if int(racer.member.id) == int(racer_usr.id):
                return racer

# Leaderboard data
    # Returns the string to go in the topic for the leaderboard
    @property
    def leaderboard(self):
        new_leaderboard = '``` \n' + self.leaderboard_header + StatusStrs[self._status] + '\n'
        new_leaderboard += 'Entrants:\n'
        new_leaderboard += self.leaderboard_text
        new_leaderboard += '```'
        return new_leaderboard

    # Returns 'header' text for the race, giving info about the rules etc.
    @property
    def leaderboard_header(self):
        room_rider = self.room.format_rider
        if room_rider:
            room_rider = ' ' + room_rider

        seed_str = self.race_info.seed_str
        if seed_str:
            seed_str = '\n' + seed_str

        return self.race_info.format_str + room_rider + seed_str + '\n'

    # Returns a list of racers and their statuses.
    @property
    def leaderboard_text(self, shortened=False):
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
            return self.leaderboard_text(shortened=True)
        else:
            return text

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
            asyncio.ensure_future(self.room.update_leaderboard())

    # Pause the race timer.
    async def pause(self):
        if self._status == RaceStatus.racing:
            self._status = RaceStatus.paused
            self._last_pause_time = time.monotonic()
            asyncio.ensure_future(self.room.update_leaderboard())
            return True
        return False

    # Unpause the race timer.
    async def unpause(self):
        if self._status == RaceStatus.paused:
            self._status = RaceStatus.racing
            self._adj_start_time += time.monotonic() - self._last_pause_time
            asyncio.ensure_future(self.room.update_leaderboard())
            return True
        return False

    # Enters the given discord Member in the race
    async def enter_member(self, racer_member):
        if self.has_racer(racer_member):
            await self.room.write('{0} is already entered.'.format(racer_member.mention))

        elif self._status == RaceStatus.counting_down:
            await self._cancel_countdown()

        elif not self.before_race:
            await self.room.write('{0}: Cannot enter; the race has already started.'.format(racer_member.mention))
            return

        else:
            self._do_enter_racer(racer_member)
            await self.room.write(
                '{0} has entered the race. {1} entrants.'.format(racer_member.mention, len(self.racers)))
            asyncio.ensure_future(self.room.update_leaderboard())

    # Unenters the given discord Member in the race
    async def unenter_member(self, racer_member):
        self.room.dont_notify(racer_member)

        if not self.before_race:
            await self.forfeit_member(racer_member)
            return

        if self.has_racer(racer_member):
            self.racers = [r for r in self.racers if int(r.member.id) != int(racer_member.id)]
            if not self.racers:
                self._last_no_entrants_time = time.monotonic()
            if (len(self.racers) < 2 and Config.REQUIRE_AT_LEAST_TWO_FOR_RACE) or len(self.racers) < 1:
                await self._cancel_countdown()
            await self.room.write('{0} is no longer entered.'.format(racer_member.mention))
            await self.begin_if_ready()
            asyncio.ensure_future(self.room.update_leaderboard())
        else:
            await self.room.write('{0} is not entered.'.format(racer_member.mention))

    # Enters the racer if not entered, and puts that racer in the 'ready' state
    async def enter_and_ready_member(self, racer_member):
        if self._status == RaceStatus.counting_down:
            await self._cancel_countdown()

        if not self.before_race:
            await self.room.write('{0}: Cannot enter; the race has already started.'.format(racer_member.mention))
            return

        had_to_enter = False
        if not self.has_racer(racer_member):
            self._do_enter_racer(racer_member)
            had_to_enter = True

        racer = self.get_racer(racer_member)
        if racer is None:
            await self.room.write('Unexpected error.')
            console.error("Unexpected error in race.race.Race.enter_and_ready_member: "
                          "Couldn't find a Racer for the discord Member {0}.".format(racer_member.name))
            return

        if racer.is_ready:
            await self.room.write('{0} is already ready!'.format(racer_member.mention))
            return

        racer.ready()

        if len(self.racers) == 1 and Config.REQUIRE_AT_LEAST_TWO_FOR_RACE:
            await self.room.write(
                'Waiting on at least one other person to join the race.')
        elif had_to_enter:
            await self.room.write(
                '{0} has entered and is ready! {1} remaining.'.format(racer_member.mention, self.num_not_ready))
        else:
            await self.room.write(
                '{0} is ready! {1} remaining.'.format(racer_member.mention, self.num_not_ready))

        await self.begin_if_ready()

    # Attempt to put the given Racer in the 'unready' state if they were ready
    async def unready_member(self, racer_member):
        if not self.before_race:
            return

        racer = self.get_racer(racer_member)
        if racer is None:
            await self.room.write('{0}: Warning: You have not yet entered the race.'.format(racer_member.mention))
            return

        # See if we can cancel a countdown. If cancel_countdown() returns False,
        # then there is a countdown and we failed to cancel it, so racer cannot be made unready.
        success = await self._cancel_countdown()
        if success and racer.unready():
            await self.room.write('{0} is no longer ready.'.format(racer_member.mention))
            asyncio.ensure_future(self.room.update_leaderboard())
        else:
            await self.room.write("Can't unready!")

    # Puts the given Racer in the 'finished' state and gets their time
    async def finish_member(self, racer_member):
        if not self._status == RaceStatus.racing:
            return

        racer = self.get_racer(racer_member)
        if racer is None:
            return

        if racer.finish(self.current_time):
            await self.room.write(
                '{0} has finished in {1} place with a time of {2}.'.format(
                    racer_member.mention,
                    ordinal(self.num_finished),
                    racer.time_str))
            asyncio.ensure_future(self._check_for_race_end())
            asyncio.ensure_future(self.room.update_leaderboard())

    # Attempt to put the given Racer in the 'racing' state if they were finished
    async def unfinish_member(self, racer_member):
        if self.before_race or self.final:
            return

        racer = self.get_racer(racer_member)
        if racer is None:
            return

        if not racer.is_finished:
            await self.room.write('{0} is still racing!'.format(racer_member.mention))

        # See if we can cancel a (possible) finalization. If cancel_finalization() returns False,
        # then there is a finalization and we failed to cancel it, so racer cannot be made unready.
        success = await self._cancel_finalization()
        if success and racer.unfinish():
            await self.room.write('{0} continues to race!'.format(racer_member.mention))
            asyncio.ensure_future(self.room.update_leaderboard())

    async def forfeit_racer(self, racer):
        if self.before_race or self.final:
            return

        await self._do_forfeit_racer(racer)
        await self.room.write('{0} has forfeit the race.'.format(racer.member.mention))

    # Puts the given Racer in the 'forfeit' state
    async def forfeit_member(self, racer_member):
        racer = self.get_racer(racer_member)
        if racer is not None:
            await self.forfeit_racer(racer)

    # Attempt to put the given Racer in the 'racing' state if they had forfeit
    async def unforfeit_member(self, racer_member):
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
            await self.room.write('{0} is no longer forfeit and continues to race!'.format(racer_member.mention))
            asyncio.ensure_future(self.room.update_leaderboard())

    # Forfeits all racers that have not yet finished
    async def forfeit_all_remaining(self):
        if not self.before_race:
            for racer in self.racers:
                if racer.is_racing:
                    await self._do_forfeit_racer(racer)

    # Adds the given string as a comment
    async def add_comment_for_member(self, racer_member, comment_str):
        if self.before_race or self.final:
            return

        racer = self.get_racer(racer_member)
        if racer is None:
            return

        racer.add_comment(comment_str[:255])
        asyncio.ensure_future(self.room.update_leaderboard())

    # Adds a death for the given member at the given level and causes them to forfeit
    async def set_death_for_member(self, racer_member, level):
        if self.before_race or self.final:
            return

        racer = self.get_racer(racer_member)
        if racer is None:
            return

        await self._do_forfeit_racer(racer)
        await self.room.write('{0} has forfeit the race.'.format(racer_member.mention))
        if not level == -1:
            racer.level = level

    # Adds an in-game time for the given member
    async def set_igt_for_member(self, racer_member, igt):
        if self.before_race or self.final:
            return

        racer = self.get_racer(racer_member)
        if racer is None:
            return

        if igt != -1 and racer.is_done_racing:
            racer.igt = igt
            asyncio.ensure_future(self.room.update_leaderboard())

    # Kicks the specified racers from the race (they can re-enter)
    async def kick_racers(self, names_to_kick):
        for racer in self.racers:
            if racer.name.lower() in names_to_kick:
                await self.unenter_member(racer.member)

    # Cancel the race.
    async def cancel(self):
        self._status = RaceStatus.cancelled
        await self._cancel_countdown()
        await self._cancel_finalization()
        await self.room.write('The race has been cancelled.')
        asyncio.ensure_future(self.room.update_leaderboard())

# Private methods (all coroutines)
    # Actually enter the racer
    def _do_enter_racer(self, racer_member):
        racer = Racer(racer_member)
        if racer in self.racers:
            return
        self.racers.append(racer)
        self.room.notify(racer_member)

    # Begins the race. Called by the countdown.
    async def _begin_race(self):
        for racer in self.racers:
            if not racer.begin_race():
                console.error("{} isn't ready while calling race._begin_race -- unexpected error.".format(
                    racer.name))

        self._status = RaceStatus.racing
        self._adj_start_time = time.monotonic()
        self._start_datetime = datetime.datetime.utcnow()
        await self.room.write('GO!')
        asyncio.ensure_future(self.room.update_leaderboard())

    # Checks to see if all racers have either finished or forfeited. If so, ends the race.
    # Return True if race was ended.
    async def _check_for_race_end(self):
        for racer in self.racers:
            if not racer.is_done_racing:
                return False

        await self._end_race()
        return True

    # Ends the race, and begins a countdown until the results are 'finalized'
    async def _end_race(self):
        if self._status == RaceStatus.racing:
            self._status = RaceStatus.completed
            self._finalize_future = asyncio.ensure_future(self._finalization_countdown())

    # Countdown coroutine to be wrapped in self._countdown_future.
    # Warning: Do not call this -- use begin_countdown instead.
    async def _race_countdown(self):
        countdown_systemtime_begin = time.monotonic()
        countdown_timer = Config.COUNTDOWN_LENGTH
        await asyncio.sleep(1)      # Pause before countdown

        await self.room.write('The race will begin in {0} seconds.'.format(countdown_timer))
        while countdown_timer > 0:
            if countdown_timer <= Config.INCREMENTAL_COUNTDOWN_START:
                await self.room.write('{}'.format(countdown_timer))
            sleep_time = countdown_systemtime_begin + Config.COUNTDOWN_LENGTH - countdown_timer + 1 - time.monotonic()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)         # sleep until the next tick
            countdown_timer -= 1

        # Begin the race.
        await self._begin_race()

    # Countdown coroutine to be wrapped in self._finalize_future.
    # Warning: Do not call this -- use end_race instead.
    async def _finalization_countdown(self):
        await asyncio.sleep(1)      # Waiting for a short time feels good UI-wise
        await self.room.write(
            'The race is over. Results will be recorded in {} seconds. Until then, you may comment with `.comment '
            '[text]` or add an in-game-time with `.igt [time]`.'.format(Config.FINALIZE_TIME_SEC))

        self.delay_record = True
        while self.delay_record:
            self.delay_record = False
            await asyncio.sleep(Config.FINALIZE_TIME_SEC)

        # Perform the finalization and record the race. At this point, the finalization cannot be cancelled.
        self._status = RaceStatus.finalized
        time_str = self.start_datetime.strftime("%d %B %Y, UTC %H:%M")
        await self.room.post_result(
            'Race begun at {0}:\n```\n{1}{2}\n```'.format(
                time_str, self.leaderboard_header, self.leaderboard_text))

        NecroDB().record_race(self)

    # Attempt to cancel the race countdown -- transition race state from 'counting_down' to 'entry_open'
    # Returns False only if there IS a countdown, AND we failed to cancel it
    async def _cancel_countdown(self, display_msgs=True):
        if self._status == RaceStatus.counting_down:
            if self._countdown_future:
                if self._countdown_future.cancel():
                    self._countdown_future = None
                    self._status = RaceStatus.entry_open
                    asyncio.ensure_future(self.room.update_leaderboard())
                    if display_msgs:
                        await self.room.write('Countdown cancelled.')
                    return True
                else:
                    return False
        return True

    # Attempt to cancel finalization and restart race -- transition race state from 'completed' to 'racing'
    # Returns False only if race IS completed, AND we failed to restart it
    async def _cancel_finalization(self, display_msgs=True):
        if self._status == RaceStatus.completed:
            if self._finalize_future:
                if self._finalize_future.cancel():
                    self._finalize_future = None
                    self._status = RaceStatus.racing
                    asyncio.ensure_future(self.room.update_leaderboard())
                    if display_msgs:
                        await self.room.write('Race end cancelled -- unfinished racers may continue!')
                    return True
                else:
                    return False
        return True

    # Causes the racer to forfeit and prints a message if successful
    async def _do_forfeit_racer(self, racer):
        if racer.forfeit(self.current_time):
            asyncio.ensure_future(self._check_for_race_end())
            asyncio.ensure_future(self.room.update_leaderboard())
