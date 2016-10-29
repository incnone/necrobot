# Commands for within a race room

import asyncio

from ..command import command
from ..race import racetime
from ..util import config
from ..util import level

SUFFIXES = {1: 'st', 2: 'nd', 3: 'rd'}
def ordinal(num):
    if 10 <= num % 100 <= 20:
        suffix = 'th'
    else:
        suffix = SUFFIXES.get(num % 10, 'th')
    return str(num) + suffix

class Enter(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'enter', 'join', 'e', 'j')
        self.help_text = 'Enters (registers for) the race. After entering, use `.ready` to indicate you are ready to begin the race. You may use `.join` instead of `.enter` if preferred.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if not self._room.race.is_before_race:
            return

        new_entry = yield from self._room.race.enter_racer(command.author)
        if new_entry:
            self._room.notify(command.author)
            yield from self._room.write('{0} has entered the race. {1} entrants.'.format(command.author.mention, len(self._room.race.racers)))
        else:
            yield from self._room.write('{0} is already entered.'.format(command.author.mention))

class Unenter(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'unenter', 'unjoin')
        self.help_text = 'Leaves the race. You may use `.unjoin` instead of `.unenter` if preferred.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if not self._room.race.is_before_race:
            return

        self._room.dont_notify(command.author)
        success = yield from self._room.race.unenter_racer(command.author)
        if success:
            yield from self._room.write('{0} is no longer entered.'.format(command.author.mention))
            yield from self._room.begin_if_ready()

class Ready(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'ready', 'r')
        self.help_text = 'Indicates that you are ready to begin the race. The race begins when all entrants are ready.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if not self._room.race.is_before_race:
            return

        racer = self._room.race.get_racer(command.author)
        if racer:
            success = yield from self._room.race.ready_racer(racer)    #success is True if the racer was unready and now is ready
            if success:
                if len(self._room.race.racers) == 1 and config.REQUIRE_AT_LEAST_TWO_FOR_RACE:
                    yield from self._room.write('Waiting on at least one other person to join the race.')
                else:
                    yield from self._room.write('{0} is ready! {1} remaining.'.format(command.author.mention, self._room.race.num_not_ready))

                yield from self._room.begin_if_ready()

            elif racer.is_ready:
                yield from self._room.write('{0} is already ready!'.format(command.author.mention))
        else:
            yield from self._room.write('{}: Please `.enter` the race before readying.'.format(command.author.mention))

class Unready(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'unready')
        self.help_text = 'Undoes `.ready`.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if not self._room.race.is_before_race:
            return

        racer = self._room.race.get_racer(command.author)
        if racer:
            success = yield from self._room.race.unready_racer(racer)  #success is True if the racer was ready and now is unready
            #NB: success might be False even in reasonable-use contexts, e.g., if the countdown fails to cancel
            if success:
                yield from self._room.write('{0} is no longer ready.'.format(command.author.mention))
        else:
            yield from self._room.write('{}: Warning: You have not yet entered the race.'.format(command.author.mention))

class Done(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'done', 'finish', 'd')
        self.help_text = 'Indicates you have finished the race goal, and gets your final time. You may instead use `.finish` if preferred.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            return

        racer = self._room.race.get_racer(command.author)
        if racer:
            success = yield from self._room.race.finish_racer(racer) #success is true if the racer was racing and is now finished
            if success:
                num_finished = self._room.race.num_finished
                yield from self._room.write('{0} has finished in {1} place with a time of {2}.'.format(command.author.mention, ordinal(num_finished), racer.time_str))

class Undone(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'undone', 'unfinish')
        self.help_text = 'Undoes an earlier `.done`.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            return

        success = yield from self._room.race.unfinish_racer(self._room.race.get_racer(command.author)) #success is true if the racer was finished and now is not
        #NB: success might be False even in reasonable-use contexts, e.g., if the race became finalized
        if success:
            yield from self._room.write('{} is no longer done and continues to race.'.format(command.author.mention))

class Forfeit(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'forfeit', 'quit', 'f', 'q')
        self.help_text = 'Forfeits from the race. You may use `.quit` instead of `.forfeit` if preferred.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            return

        success = yield from self._room.race.forfeit_racer(self._room.race.get_racer(command.author)) #success is True if the racer was racing and is now forfeit
        if success:
            yield from self._room.write('{} has forfeit the race.'.format(command.author.mention))

        if len(command.args) > 0:
            racer = self._room.race.get_racer(command.author)
            if racer:
                cut_length = len(command.command) + len(config.BOT_COMMAND_PREFIX) + 1
                end_length = 255 + cut_length
                racer.add_comment(command.message.content[cut_length:end_length])
                asyncio.ensure_future(self._room.update_leaderboard())

class Unforfeit(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'unforfeit', 'unquit')
        self.help_text = 'Undoes an earlier `.forfeit`.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            return

        success = yield from self._room.race.unforfeit_racer(self._room.race.get_racer(command.author)) #success is true if the racer was forfeit and now is not
        #NB: success might be False even in reasonable-use contexts, e.g., if the race became finalized
        if success:
            yield from self._room.write('{} is no longer forfeit and continues to race.'.format(command.author.mention))

class Comment(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'comment', 'c')
        self.help_text = 'Adds text as a comment to your race.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            return

        racer = self._room.race.get_racer(command.author)
        if racer:
            cut_length = len(command.command) + len(config.BOT_COMMAND_PREFIX) + 1
            end_length = 255 + cut_length
            racer.add_comment(command.message.content[cut_length:end_length])
            asyncio.ensure_future(self._room.update_leaderboard())

class Death(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'death')
        self.help_text = 'Marks your race as having died at a given level, e.g., `{} 3-2`.'.format(self.mention)
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            return

        if len(command.args) == 1:
            lvl = level.from_str(command.args[0])
            racer = self._room.race.get_racer(command.author)
            if lvl != -1 and racer:
                success = yield from self._room.race.forfeit_racer(self._room.race.get_racer(command.author))
                racer.level = lvl
                if success:
                    asyncio.ensure_future(self._room.update_leaderboard())
                    yield from self._room.write('{} has forfeit the race.'.format(command.author.mention))

class Igt(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'igt')
        self.help_text = 'Adds an in-game-time to your race, e.g. `{} 12:34.56.`'.format(self.mention)
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            return

        if len(command.args) == 1:
            igt = racetime.from_str(command.args[0])
            racer = self._room.race.get_racer(command.author)
            if igt != -1 and racer and racer.is_done_racing:
                racer.igt = igt
                asyncio.ensure_future(self._room.update_leaderboard())

class Rematch(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'rematch', 're', 'rm')
        self.help_text = 'If the race is complete, creates a new race with the same rules in a separate room.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            yield from self._room.write('{}: Maybe we should do this race first.'.format(command.author.mention))
        elif self._room.race.complete:
            yield from self._room.make_rematch()
        else:
            yield from self._room.write('{}: The current race has not yet ended!'.format(command.author.mention))

class DelayRecord(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'delayrecord')
        self.help_text = 'If the race is complete, delays recording of the race for some extra time.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if not self._room.race.complete:
            return

        if not self._room.race.delay_record:
            self._room.race.delay_record = True
            yield from self._room.write('Delaying recording for an extra {} seconds.'.format(config.FINALIZE_TIME_SEC))
        else:
            yield from self._room.write('Recording is already delayed.')

class Notify(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'notify')
        self.help_text = 'If a rematch of this race is made, you will be @mentioned at the start of its channel. Use `.notify off` to cancel this.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if len(command.args) == 1 and command.args[0] == 'off':
            self._room.dont_notify(command.author)
            yield from self._room.write('{0}: You will not be alerted when a rematch begins.'.format(command.author.mention))
        elif len(command.args) == 0 or (len(command.args) == 1 and command.args[1] == 'on'):
            self._room.notify(command.author)
            yield from self._room.write('{0}: You will be alerted when a rematch begins.'.format(command.author.mention))

class Time(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'time')
        self.help_text = 'Get the current race time.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.is_before_race:
            yield from self._room.write('The race hasn\'t started.')
        elif self._room.race.complete:
            yield from self._room.write('The race is over.')
        else:
            yield from self._room.write('The current race time is {}.'.format(self._room.race.current_time_str))

class Missing(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'missing')
        self.help_text = 'List users that were notified but have not yet entered.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        missing_usernames = ''
        for user in self._room.mentioned_users:
            user_entered = False
            for racer in self._room.race.racers.values():
                if int(racer.member.id) == int(user.id):
                    user_entered = True
                    break
            if not user_entered:
                missing_usernames += user.name + ', '
        if missing_usernames:
            yield from self._room.write('Missing: {0}.'.format(missing_usernames[:-2]))
        else:
            yield from self._room.write('No one missing!')

class Shame(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'shame')
        self.help_text = ''
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        yield from self._room.write('Shame on you {0}!'.format(command.author))

class Poke(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'poke')
        self.help_text = 'If only one, or fewer than 1/4, of the racers are unready, this command @mentions them.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if not self._room.race.is_before_race:
            return

        yield from self._room.poke()

class ForceCancel(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'forcecancel')
        self.help_text = 'Cancels the race.'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            yield from self._room.race.cancel()

class ForceClose(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'forceclose')
        self.help_text = 'Cancel the race, and close the channel.'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            yield from self._room.close()

class ForceForfeit(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'forceforfeit')
        self.help_text = 'Force the given racer to forfeit the race (even if they have finished).'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author) and not self._room.race.is_before_race:
            for name in command.args:
                for racer in self._room.race.racers.values():
                    if racer.name.lower() == name.lower():
                        asyncio.ensure_future(self._room.race.forfeit_racer(racer))

class ForceForfeitAll(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'forceforfeitall')
        self.help_text = 'Force all unfinished racers to forfeit the race.'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author) and not self._room.race.is_before_race:
            for racer in self._room.race.racers.values():
                if racer.is_racing:
                    asyncio.ensure_future(self._room.race.forfeit_racer(racer))

class ForceRecord(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'forcerecord')
        self.help_text = 'Force the race to finalize and record.'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author) and self._room.race.complete:
            yield from self._room.race.record()
            yield from self._room.write('Race recorded.')

class Kick(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'kick')
        self.help_text = 'Remove a racer from the race. (They can still re-enter with `.enter`.'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            names_to_kick = [n.lower() for n in command.args]
            racers = self._room.race.racers.values()
            for racer in racers:
                if racer.name.lower() in names_to_kick:
                    success = yield from self._room.race.unenter_racer(racer)
                    if success:
                        yield from self._room.write('Kicked {} from the race.'.format(racer.name))

