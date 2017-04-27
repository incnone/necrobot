# General cmds for any BotChannel that runs races. The BotChannel should implement:
#     current_race -> Race       : Gets the "current" race (for Enter/Ready)
#     last_begun_race -> Race    : Gets the race that most recently started (GO!), or None if no such
#     change_race_info(RaceInfo) : Changes the type of races run in the BotChannel
#     write(str)                 : Writes a message to the BotChannel
# Remarks:
#     - change_race_info is only required for ChangeRace
#     - write is only required for Time

import necrobot.exception
from necrobot.util import level, racetime

from necrobot.botbase.commandtype import CommandType


class Enter(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'enter', 'join', 'e', 'j')
        self.help_text = 'Enters (registers for) the race. After entering, use `.ready` to indicate you are ready to ' \
                         'begin the race.'

    async def _do_execute(self, cmd):
        await self.bot_channel.current_race.enter_member(cmd.author)


class Unenter(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'unenter', 'unjoin')
        self.help_text = 'Leaves the race.'

    async def _do_execute(self, cmd):
        await self.bot_channel.current_race.unenter_member(cmd.author)


class Ready(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'ready', 'r')
        self.help_text = 'Indicates that you are ready to begin the race. The race begins when all entrants are ready.'

    async def _do_execute(self, cmd):
        await self.bot_channel.current_race.enter_and_ready_member(cmd.author)


class Unready(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'unready')
        self.help_text = 'Undoes `.ready`.'

    async def _do_execute(self, cmd):
        await self.bot_channel.current_race.unready_member(cmd.author)


class Done(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'done', 'finish', 'd')
        self.help_text = 'Indicates you have finished the race goal, and gets your final time. '

    async def _do_execute(self, cmd):
        # Override: parse .d X-Y as a death
        if len(cmd.args) >= 1 and cmd.command == 'd':
            lvl = level.from_str(cmd.args[0])
            if lvl != level.LEVEL_NOS:
                await self.reparse_as('death', cmd)
                return

        await self.bot_channel.current_race.finish_member(cmd.author)


class Undone(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'undone', 'unfinish')
        self.help_text = 'Undoes an earlier `.done`.'

    async def _do_execute(self, cmd):
        await self.bot_channel.current_race.unfinish_member(cmd.author)


class Forfeit(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'forfeit', 'quit', 'f', 'q')
        self.help_text = 'Forfeits from the race.'

    async def _do_execute(self, cmd):
        await self.bot_channel.current_race.forfeit_member(cmd.author)
        
        if len(cmd.args) >= 1:
            if self.bot_channel.last_begun_race is None:
                return
            lvl = level.from_str(cmd.args[0])
            await self.bot_channel.last_begun_race.set_death_for_member(cmd.author, lvl)
            if len(cmd.args) >= 2:
                cmd.args.pop(0)
                await self.reparse_as('comment', cmd)

            await self.reparse_as('comment', cmd)


class Unforfeit(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'unforfeit', 'unquit')
        self.help_text = 'Undoes an earlier `.forfeit`.'

    async def _do_execute(self, cmd):
        await self.bot_channel.current_race.unforfeit_member(cmd.author)


class Comment(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'comment', 'c')
        self.help_text = 'Adds text as a comment to your race.'

    async def _do_execute(self, cmd):
        if self.bot_channel.last_begun_race is None:
            return

        await self.bot_channel.last_begun_race.add_comment_for_member(
            cmd.author,
            cmd.arg_string
        )


class Death(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'death')
        self.help_text = 'Marks your race as having died at a given level, e.g., `{} 3-2`.'.format(self.mention)

    async def _do_execute(self, cmd):
        if len(cmd.args) == 0:
            await self.reparse_as('forfeit', cmd)
        else:
            if self.bot_channel.last_begun_race is None:
                return
            lvl = level.from_str(cmd.args[0])
            await self.bot_channel.last_begun_race.set_death_for_member(cmd.author, lvl)
            if len(cmd.args) >= 2:
                cmd.args.pop(0)
                await self.reparse_as('comment', cmd)


class Igt(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'igt')
        self.help_text = 'Adds an in-game-time to your race, e.g. `{} 12:34.56.`'.format(self.mention)

    async def _do_execute(self, cmd):
        if self.bot_channel.last_begun_race is None:
            return

        if len(cmd.args) == 1:
            igt = racetime.from_str(cmd.args[0])
            await self.bot_channel.last_begun_race.set_igt_for_member(cmd.author, igt)


class Time(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'time')
        self.help_text = 'Get the current race time.'

    async def _do_execute(self, cmd):
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

    async def _do_execute(self, cmd):
        if self.bot_channel.last_begun_race is None:
            return

        for name in cmd.args:
            for racer in self.bot_channel.last_begun_race.racers:
                if racer.name.lower() == name.lower():
                    await self.bot_channel.last_begun_race.forfeit_racer(racer)


class ForceForfeitAll(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'forceforfeitall')
        self.help_text = 'Force all unfinished racers to forfeit the race.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        if self.bot_channel.last_begun_race is None:
            return

        await self.bot_channel.last_begun_race.forfeit_all_remaining()


class Reseed(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'reseed')
        self.help_text = 'Randomly generate a new seed for this race.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        await self.bot_channel.current_race.reseed()


class Pause(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'pause', 'p')
        self.help_text = 'Pause the race timer.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        await self.bot_channel.current_race.pause()


class Unpause(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'unpause')
        self.help_text = 'Unpause the race timer.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        await self.bot_channel.current_race.unpause()


class ChangeRules(CommandType):
    def __init__(self, race_room):
        CommandType.__init__(self, race_room, 'changerules')
        self.help_text = 'Change the rules for the race. Takes the same parameters as `.make`.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        try:
            await self.bot_channel.change_race_info(cmd.args)
        except necrobot.exception.ParseException as e:
            await self.client.send_message(
                cmd.channel,
                "Couldn't parse input: `{0}`.".format(e)
            )
