# Commands for within a race room

from ..command.command import CommandType
from ..race import racetime
from ..util.config import Config
from ..util import level


class Enter(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'enter', 'join', 'e', 'j')
        self.help_text = 'Enters (registers for) the race. After entering, use `.ready` to indicate you are ready to ' \
                         'begin the race. You may use `.join` instead of `.enter` if preferred.'

    async def _do_execute(self, command):
        await self.bot_channel.current_race.enter_member(command.author)


class Unenter(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'unenter', 'unjoin')
        self.help_text = 'Leaves the race. You may use `.unjoin` instead of `.unenter` if preferred.'

    async def _do_execute(self, command):
        await self.bot_channel.current_race.unenter_member(command.author)


class Ready(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'ready', 'r')
        self.help_text = 'Indicates that you are ready to begin the race. The race begins when all entrants are ready.'

    async def _do_execute(self, command):
        await self.bot_channel.current_race.enter_and_ready_member(command.author)


class Unready(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'unready')
        self.help_text = 'Undoes `.ready`.'

    async def _do_execute(self, command):
        await self.bot_channel.current_race.unready_member(command.author)


class Done(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'done', 'finish', 'd')
        self.help_text = 'Indicates you have finished the race goal, and gets your final time. ' \
                         'You may instead use `.finish` if preferred.'

    async def _do_execute(self, command):
        await self.bot_channel.current_race.finish_member(command.author)


class Undone(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'undone', 'unfinish')
        self.help_text = 'Undoes an earlier `.done`.'

    async def _do_execute(self, command):
        await self.bot_channel.current_race.unfinish_member(command.author)


class Forfeit(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'forfeit', 'quit', 'f', 'q')
        self.help_text = 'Forfeits from the race. You may use `.quit` instead of `.forfeit` if preferred.'

    async def _do_execute(self, command):
        await self.bot_channel.current_race.forfeit_member(command.author)


class Unforfeit(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'unforfeit', 'unquit')
        self.help_text = 'Undoes an earlier `.forfeit`.'

    async def _do_execute(self, command):
        await self.bot_channel.current_race.unforfeit_member(command.author)


class Comment(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'comment', 'c')
        self.help_text = 'Adds text as a comment to your race.'

    async def _do_execute(self, command):
        if self.bot_channel.last_begun_race is None:
            return

        cut_length = len(command.command) + len(Config.BOT_COMMAND_PREFIX) + 1
        await self.bot_channel.last_begun_race.add_comment_for_member(command.author, command.message.content[cut_length:])


class Death(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'death')
        self.help_text = 'Marks your race as having died at a given level, e.g., `{} 3-2`.'.format(self.mention)

    async def _do_execute(self, command):
        if self.bot_channel.last_begun_race is None:
            return

        if len(command.args) == 1:
            lvl = level.from_str(command.args[0])
            await self.bot_channel.last_begun_race.set_death_for_member(command.author, lvl)


class Igt(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'igt')
        self.help_text = 'Adds an in-game-time to your race, e.g. `{} 12:34.56.`'.format(self.mention)

    async def _do_execute(self, command):
        if self.bot_channel.last_begun_race is None:
            return

        if len(command.args) == 1:
            igt = racetime.from_str(command.args[0])
            await self.bot_channel.last_begun_race.set_igt_for_member(command.author, igt)


class Rematch(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'rematch', 're', 'rm')
        self.help_text = 'If the race is complete, creates a new race with the same rules in a separate room.'

    async def _do_execute(self, command):
        if self.bot_channel.current_race.complete:
            await self.bot_channel.make_rematch()
        elif not self.bot_channel.current_race.before_race:
            await self.bot_channel.write('{}: The current race has not yet ended!'.format(command.author.mention))


class DelayRecord(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'delayrecord')
        self.help_text = 'If the race is complete, delays recording of the race for some extra time.'

    async def _do_execute(self, command):
        if self.bot_channel.last_begun_race is None or (not self.bot_channel.last_begun_race.complete):
            return

        if not self.bot_channel.last_begun_race.delay_record:
            self.bot_channel.last_begun_race.delay_record = True
            await self.bot_channel.write('Delaying recording for an extra {} seconds.'.format(Config.FINALIZE_TIME_SEC))
        else:
            await self.bot_channel.write('Recording is already delayed.')


class Notify(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'notify')
        self.help_text = 'If a rematch of this race is made, you will be @mentioned at the start of its channel. ' \
                         'Use `.notify off` to cancel this.'

    async def _do_execute(self, command):
        if len(command.args) == 1 and command.args[0] == 'off':
            self.bot_channel.dont_notify(command.author)
            await self.bot_channel.write('{0}: You will not be alerted when a rematch begins.'.format(command.author.mention))
        elif len(command.args) == 0 or (len(command.args) == 1 and command.args[1] == 'on'):
            self.bot_channel.notify(command.author)
            await self.bot_channel.write('{0}: You will be alerted when a rematch begins.'.format(command.author.mention))


class Time(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'time')
        self.help_text = 'Get the current race time.'

    async def _do_execute(self, command):
        if self.bot_channel.current_race.before_race:
            await self.bot_channel.write('The race hasn\'t started.')
        elif self.bot_channel.current_race.complete:
            await self.bot_channel.write('The race is over.')
        else:
            await self.bot_channel.write('The current race time is {}.'.format(self.bot_channel.last_begun_race.current_time_str))


class Missing(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'missing')
        self.help_text = 'List users that were notified but have not yet entered.'

    async def _do_execute(self, command):
        missing_usernames = ''
        for user in self.bot_channel.mentioned_users:
            user_entered = False
            for racer in self.bot_channel.last_begun_race.racers:
                if int(racer.member.id) == int(user.id):
                    user_entered = True
                    break
            if not user_entered:
                missing_usernames += user.display_name + ', '
        if missing_usernames:
            await self.bot_channel.write('Missing: {0}.'.format(missing_usernames[:-2]))
        else:
            await self.bot_channel.write('No one missing!')


class Shame(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'shame')
        self.help_text = ''
        self.secret_command = True

    async def _do_execute(self, command):
        await self.bot_channel.write('Shame on you {0}!'.format(command.author.display_name))


class Poke(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'poke')
        self.help_text = 'If only one, or fewer than 1/4, of the racers are unready, this command @mentions them.'

    async def _do_execute(self, command):
        await self.bot_channel.poke()


class ForceCancel(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'forcecancel')
        self.help_text = 'Cancels the race.'
        self.admin_only = True

    async def _do_execute(self, command):
        if self.bot_channel.last_begun_race is not None:
            await self.bot_channel.last_begun_race.cancel()
        else:
            await self.bot_channel.close()


class ForceClose(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'forceclose')
        self.help_text = 'Cancel the race, and close the channel.'
        self.admin_only = True

    async def _do_execute(self, command):
        await self.bot_channel.close()


class ForceForfeit(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'forceforfeit')
        self.help_text = 'Force the given racer to forfeit the race (even if they have finished).'
        self.admin_only = True

    async def _do_execute(self, command):
        if self.bot_channel.last_begun_race is None:
            return

        for name in command.args:
            for racer in self.bot_channel.last_begun_race.racers:
                if racer.name.lower() == name.lower():
                    await self.bot_channel.last_begun_race.forfeit_racer(racer)


class ForceForfeitAll(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'forceforfeitall')
        self.help_text = 'Force all unfinished racers to forfeit the race.'
        self.admin_only = True

    async def _do_execute(self, command):
        if self.bot_channel.last_begun_race is None:
            return

        await self.bot_channel.last_begun_race.forfeit_all_remaining()


class Kick(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'kick')
        self.help_text = 'Remove a racer from the race. (They can still re-enter with `.enter`.)'
        self.admin_only = True

    async def _do_execute(self, command):
        names_to_kick = [n.lower() for n in command.args]
        await self.bot_channel.current_race.kick_racers(names_to_kick)


class Reseed(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'reseed')
        self.help_text = 'Randomly generate a new seed for this race.'
        self.admin_only = True

    async def _do_execute(self, command):
        await self.bot_channel.reseed()


class Pause(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'pause', 'p')
        self.help_text = 'Pause the race timer.'
        self.admin_only = True

    async def _do_execute(self, command):
        success = await self.bot_channel.pause()
        if success:
            await self.bot_channel.write('Race paused by {}!'.format(command.author.mention))


class Unpause(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'unpause')
        self.help_text = 'Unpause the race timer.'
        self.admin_only = True

    async def _do_execute(self, command):
        await self.bot_channel.unpause()


class ChangeRules(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'changerules')
        self.help_text = 'Change the rules for the race. Takes the same parameters as `.make`.'
        self.admin_only = True

    async def _do_execute(self, command):
        await self.bot_channel.change_race_info(command.args)
