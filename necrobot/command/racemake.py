import discord
import logging

from .command import CommandType
from ..race import raceinfo, privateraceinfo


class Make(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'make')
        self.help_text = \
            "Create a new race room. By default this creates an unseeded Cadence race, " \
            "but there are optional parameters. First, the short form:\n" \
            "```" \
            ".make [char] [u|s]" \
            "```" \
            "makes a race with the given character and seeding options; `char` should be a Necrodancer character, " \
            "and the other field is either the letter `u` or the letter `s`, according to whether the race should be " \
            "seeded or unseeded. Examples: `.make dorian u` or `.make s dove` are both fine.\n" \
            "\n" \
            "More options are available using usual command-line syntax:" \
            "```" \
            ".make [-c char] [-u|-s|-seed number] [-custom desc]" \
            "```" \
            "makes a race with character char, and seeded/unseeded determined by the `-u` or `-s` flag. If instead a " \
            "number is specified, the race will be seeded and forced to use the seed given. The number must be an " \
            "integer (text seeds are not supported). " \
            "Finally, desc allows you to give any custom one-word description of the race (e.g., '4-shrine')."

    async def _do_execute(self, command):
        race_info = raceinfo.parse_args(command.args)
        if race_info:
            try:
                await self.necrobot.race_manager.make_room(race_info)
            except discord.HTTPException as e:
                await self.necrobot.client.send_message(command.channel, 'Error making race.')
                logging.getLogger('discord').warning(e.response)


class MakePrivate(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'makeprivate')
        self.help_text = "Create a new private race room. This takes the same command-line options as `.make`."

    async def _do_execute(self, command):
        try:
            cmd_idx = command.args.index('-repeat')
            repeat_index = int(command.args[cmd_idx + 1])
            del command.args[cmd_idx + 1]
            del command.args[cmd_idx]
        except (ValueError, IndexError):
            repeat_index = 1

        private_race_info = privateraceinfo.parse_args(command.args)
        if private_race_info is not None:
            for _ in range(repeat_index):
                await self.necrobot.race_manager.make_private_room(private_race_info, command.author)
        else:
            await self.necrobot.client.send_message(
                command.channel, 'Error parsing arguments to `.makeprivate`.')
