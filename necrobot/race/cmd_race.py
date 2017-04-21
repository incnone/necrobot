# General commands for any BotChannel that runs races. The BotChannel should implement:
#     current_race -> Race       : Gets the "current" race (for Enter/Ready)
#     last_begun_race -> Race    : Gets the race that most recently started (GO!), or None if no such
#     change_race_info(RaceInfo) : Changes the type of races run in the BotChannel
#     write(str)                 : Writes a message to the BotChannel
# Remarks:
#     - change_race_info is only required for ChangeRace
#     - write is only required for Time

from necrobot.race import racetime
from necrobot.util import level

from necrobot.botbase.command import CommandType
from necrobot.util.config import Config


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
        await self.bot_channel.last_begun_race.add_comment_for_member(
            command.author,
            command.message.content[cut_length:])


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
            await self.bot_channel.write(
                'The current race time is {}.'.format(self.bot_channel.last_begun_race.current_time_str))


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


class Reseed(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'reseed')
        self.help_text = 'Randomly generate a new seed for this race.'
        self.admin_only = True

    async def _do_execute(self, command):
        await self.bot_channel.current_race.reseed()


class Pause(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'pause', 'p')
        self.help_text = 'Pause the race timer.'
        self.admin_only = True

    async def _do_execute(self, command):
        await self.bot_channel.current_race.pause()


class Unpause(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'unpause')
        self.help_text = 'Unpause the race timer.'
        self.admin_only = True

    async def _do_execute(self, command):
        await self.bot_channel.current_race.unpause()


class ChangeRules(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'changerules')
        self.help_text = 'Change the rules for the race. Takes the same parameters as `.make`.'
        self.admin_only = True

    async def _do_execute(self, command):
        await self.bot_channel.change_race_info(command.args)
