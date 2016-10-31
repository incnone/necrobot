# Commands for within a race room

from ..command.command import CommandType
from ..race import racetime
from ..util.config import Config
from ..util import level


class Enter(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'enter', 'join', 'e', 'j')
        self._room = race_room
        self.help_text = 'Enters (registers for) the race. After entering, use `.ready` to indicate you are ready to ' \
                         'begin the race. You may use `.join` instead of `.enter` if preferred.'

    async def _do_execute(self, command):
        await self._room.current_race.enter_member(command.author)


class Unenter(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'unenter', 'unjoin')
        self._room = race_room
        self.help_text = 'Leaves the race. You may use `.unjoin` instead of `.unenter` if preferred.'

    async def _do_execute(self, command):
        await self._room.current_race.unenter_member(command.author)


class Ready(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'ready', 'r')
        self._room = race_room
        self.help_text = 'Indicates that you are ready to begin the race. The race begins when all entrants are ready.'

    async def _do_execute(self, command):
        await self._room.current_race.enter_and_ready_member(command.author)


class Unready(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'unready')
        self._room = race_room
        self.help_text = 'Undoes `.ready`.'

    async def _do_execute(self, command):
        await self._room.current_race.unready_member(command.author)


class Done(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'done', 'finish', 'd')
        self._room = race_room
        self.help_text = 'Indicates you have finished the race goal, and gets your final time. ' \
                         'You may instead use `.finish` if preferred.'

    async def _do_execute(self, command):
        await self._room.current_race.finish_member(command.author)


class Undone(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'undone', 'unfinish')
        self._room = race_room
        self.help_text = 'Undoes an earlier `.done`.'

    async def _do_execute(self, command):
        await self._room.current_race.unfinish_member(command.author)


class Forfeit(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'forfeit', 'quit', 'f', 'q')
        self._room = race_room
        self.help_text = 'Forfeits from the race. You may use `.quit` instead of `.forfeit` if preferred.'

    async def _do_execute(self, command):
        await self._room.current_race.forfeit_member(command.author)


class Unforfeit(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'unforfeit', 'unquit')
        self._room = race_room
        self.help_text = 'Undoes an earlier `.forfeit`.'

    async def _do_execute(self, command):
        await self._room.current_race.unforfeit_member(command.author)


class Comment(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'comment', 'c')
        self._room = race_room
        self.help_text = 'Adds text as a comment to your race.'

    async def _do_execute(self, command):
        if self._room.last_begun_race is None:
            return

        cut_length = len(command.command) + len(Config.BOT_COMMAND_PREFIX) + 1
        await self._room.last_begun_race.add_comment_for_member(command.author, command.message.content[cut_length:])


class Death(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'death')
        self._room = race_room
        self.help_text = 'Marks your race as having died at a given level, e.g., `{} 3-2`.'.format(self.mention)

    async def _do_execute(self, command):
        if self._room.last_begun_race is None:
            return

        if len(command.args) == 1:
            lvl = level.from_str(command.args[0])
            await self._room.last_begun_race.set_death_for_member(command.author, lvl)


class Igt(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'igt')
        self._room = race_room
        self.help_text = 'Adds an in-game-time to your race, e.g. `{} 12:34.56.`'.format(self.mention)

    async def _do_execute(self, command):
        if self._room.last_begun_race is None:
            return

        if len(command.args) == 1:
            igt = racetime.from_str(command.args[0])
            await self._room.last_begun_race.set_igt_for_member(command.author, igt)


class Rematch(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'rematch', 're', 'rm')
        self._room = race_room
        self.help_text = 'If the race is complete, creates a new race with the same rules in a separate room.'

    async def _do_execute(self, command):
        if self._room.current_race.complete:
            await self._room.make_rematch()
        elif not self._room.current_race.before_race:
            await self._room.write('{}: The current race has not yet ended!'.format(command.author.mention))


class DelayRecord(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'delayrecord')
        self._room = race_room
        self.help_text = 'If the race is complete, delays recording of the race for some extra time.'

    async def _do_execute(self, command):
        if self._room.last_begun_race is None or (not self._room.last_begun_race.complete):
            return

        if not self._room.last_begun_race.delay_record:
            self._room.last_begun_race.delay_record = True
            await self._room.write('Delaying recording for an extra {} seconds.'.format(Config.FINALIZE_TIME_SEC))
        else:
            await self._room.write('Recording is already delayed.')


class Notify(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'notify')
        self._room = race_room
        self.help_text = 'If a rematch of this race is made, you will be @mentioned at the start of its channel. ' \
                         'Use `.notify off` to cancel this.'

    async def _do_execute(self, command):
        if len(command.args) == 1 and command.args[0] == 'off':
            self._room.dont_notify(command.author)
            await self._room.write('{0}: You will not be alerted when a rematch begins.'.format(command.author.mention))
        elif len(command.args) == 0 or (len(command.args) == 1 and command.args[1] == 'on'):
            self._room.notify(command.author)
            await self._room.write('{0}: You will be alerted when a rematch begins.'.format(command.author.mention))


class Time(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'time')
        self._room = race_room
        self.help_text = 'Get the current race time.'

    async def _do_execute(self, command):
        if self._room.current_race.before_race:
            await self._room.write('The race hasn\'t started.')
        elif self._room.current_race.complete:
            await self._room.write('The race is over.')
        else:
            await self._room.write('The current race time is {}.'.format(self._room.race.current_time_str))


class Missing(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'missing')
        self._room = race_room
        self.help_text = 'List users that were notified but have not yet entered.'

    async def _do_execute(self, command):
        missing_usernames = ''
        for user in self._room.mentioned_users:
            user_entered = False
            for racer in self._room.race.racers.values():
                if int(racer.member.id) == int(user.id):
                    user_entered = True
                    break
            if not user_entered:
                missing_usernames += user.display_name + ', '
        if missing_usernames:
            await self._room.write('Missing: {0}.'.format(missing_usernames[:-2]))
        else:
            await self._room.write('No one missing!')


class Shame(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'shame')
        self._room = race_room
        self.help_text = ''
        self.secret_command = True

    async def _do_execute(self, command):
        await self._room.write('Shame on you {0}!'.format(command.author.display_name))


class Poke(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'poke')
        self._room = race_room
        self.help_text = 'If only one, or fewer than 1/4, of the racers are unready, this command @mentions them.'

    async def _do_execute(self, command):
        await self._room.poke()


class ForceCancel(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'forcecancel')
        self._room = race_room
        self.help_text = 'Cancels the race.'
        self.admin_only = True
        self._room = race_room

    async def _do_execute(self, command):
        if self._room.last_begun_race is not None:
            await self._room.last_begun_race.cancel()
        else:
            await self._room.close()


class ForceClose(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'forceclose')
        self._room = race_room
        self.help_text = 'Cancel the race, and close the channel.'
        self.admin_only = True
        self._room = race_room

    async def _do_execute(self, command):
        await self._room.close()


class ForceForfeit(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'forceforfeit')
        self._room = race_room
        self.help_text = 'Force the given racer to forfeit the race (even if they have finished).'
        self.admin_only = True

    async def _do_execute(self, command):
        if self._room.last_begun_race is None:
            return

        for name in command.args:
            for racer in self._room.last_begun_race.racers.values():
                if racer.name.lower() == name.lower():
                    await self._room.last_begun_race.forfeit_racer(racer)


class ForceForfeitAll(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'forceforfeitall')
        self._room = race_room
        self.help_text = 'Force all unfinished racers to forfeit the race.'
        self.admin_only = True

    async def _do_execute(self, command):
        if self._room.last_begun_race is None:
            return

        await self._room.last_begun_race.forfeit_all_remaining()


class Kick(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room.necrobot, 'kick')
        self._room = race_room
        self.help_text = 'Remove a racer from the race. (They can still re-enter with `.enter`.)'
        self.admin_only = True

    async def _do_execute(self, command):
        names_to_kick = [n.lower() for n in command.args]
        await self._room.current_race.kick_racers(names_to_kick)
