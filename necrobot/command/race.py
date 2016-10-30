# Commands for within a race room

import asyncio

from ..command.command import CommandType
from ..race import racetime
from ..util import config
from ..util import level


class RaceCommand(CommandType):
    def __init__(self, race_room, *args):
        CommandType.__init__(self, race_room.necrobot, args)
        self._room = race_room

    async def _do_execute(self, command):
        if self._room.race:
            await _race_do_execute(command)
        else:
            await self._room.write('No race currently in this room.')

    async def _race_do_execute(self, command):
        pass


class Enter(RaceCommand):
    def __init__(self, race_room):
        RaceCommand.__init__(self, race_room, 'enter', 'join', 'e', 'j')
        self.help_text = 'Enters (registers for) the race. After entering, use `.ready` to indicate you are ready to ' \
                         'begin the race. You may use `.join` instead of `.enter` if preferred.'

    async def _race_do_execute(self, command):
        await self._room.race.enter_member(command.author)


class Unenter(RaceCommand):
    def __init__(self, race_room):
        RaceCommand.__init__(self, race_room, 'unenter', 'unjoin')
        self.help_text = 'Leaves the race. You may use `.unjoin` instead of `.unenter` if preferred.'

    async def _race_do_execute(self, command):
        await self._room.race.unenter_member(command.author)


class Ready(RaceCommand):
    def __init__(self, race_room):
        RaceCommand.__init__(self, race_room, 'ready', 'r')
        self.help_text = 'Indicates that you are ready to begin the race. The race begins when all entrants are ready.'

    async def _race_do_execute(self, command):
        await self._room.enter_and_ready_member(command.author)


class Unready(RaceCommand):
    def __init__(self, race_room):
        RaceCommand.__init__(self, race_room, 'unready')
        self.help_text = 'Undoes `.ready`.'

    async def _race_do_execute(self, command):
        await self._room.unready_member(command.author)


class Done(RaceCommand):
    def __init__(self, race_room):
        RaceCommand.__init__(self, race_room, 'done', 'finish', 'd')
        self.help_text = 'Indicates you have finished the race goal, and gets your final time. ' \
                         'You may instead use `.finish` if preferred.'

    async def _race_do_execute(self, command):
        await self._room.finish_member(command.author)


class Undone(RaceCommand):
    def __init__(self, race_room):
        RaceCommand.__init__(self, race_room, 'undone', 'unfinish')
        self.help_text = 'Undoes an earlier `.done`.'

    async def _race_do_execute(self, command):
        await self._room.unfinish_member(command.author)


class Forfeit(RaceCommand):
    def __init__(self, race_room):
        RaceCommand.__init__(self, race_room, 'forfeit', 'quit', 'f', 'q')
        self.help_text = 'Forfeits from the race. You may use `.quit` instead of `.forfeit` if preferred.'

    async def _race_do_execute(self, command):
        await self._room.forfeit_member(command.author)


class Unforfeit(RaceCommand):
    def __init__(self, race_room):
        RaceCommand.__init__(self, race_room, 'unforfeit', 'unquit')
        self.help_text = 'Undoes an earlier `.forfeit`.'

    async def _race_do_execute(self, command):
        await self._room.unforfeit_member(command.author)


class Comment(RaceCommand):
    def __init__(self, race_room):
        RaceCommand.__init__(self, race_room, 'comment', 'c')
        self.help_text = 'Adds text as a comment to your race.'

    async def _race_do_execute(self, command):
        cut_length = len(command.command) + len(config.BOT_COMMAND_PREFIX) + 1
        await self._room.add_comment_for_member(command.author, command.message.content[cut_length:])


class Death(RaceCommand):
    def __init__(self, race_room):
        RaceCommand.__init__(self, race_room, 'death')
        self.help_text = 'Marks your race as having died at a given level, e.g., `{} 3-2`.'.format(self.mention)

    async def _race_do_execute(self, command):
        if len(command.args) == 1:
            lvl = level.from_str(command.args[0])
            await self._room.set_death_for_member(command.author, lvl)


class Igt(RaceCommand):
    def __init__(self, race_room):
        RaceCommand.__init__(self, race_room, 'igt')
        self.help_text = 'Adds an in-game-time to your race, e.g. `{} 12:34.56.`'.format(self.mention)

    async def _race_do_execute(self, command):
        if len(command.args) == 1:
            igt = racetime.from_str(command.args[0])
            await self._room.set_igt_for_member(command.author, igt)


class Rematch(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'rematch', 're', 'rm')
        self.help_text = 'If the race is complete, creates a new race with the same rules in a separate room.'
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.race.before_race:
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
        if self._room.race.before_race:
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
        if not self._room.race.before_race:
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
        if self._room.is_race_admin(command.author) and not self._room.race.before_race:
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
        if self._room.is_race_admin(command.author) and not self._room.race.before_race:
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
                    success = yield from self._room.race.unenter_member(racer)
                    if success:
                        yield from self._room.write('Kicked {} from the race.'.format(racer.name))

