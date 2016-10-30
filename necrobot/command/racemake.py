import discord
import logging

from .command import CommandType
from ..race import raceinfo


class Make(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel.necrobot, 'make')
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


# TODO private races
# class MakePrivate(command.CommandType):
#     def __init__(self, race_module):
#         command.CommandType.__init__(self, 'makeprivate')
#         self.help_text = "Create a new private race room. This takes the same command-line options as `.make`, as well as " \
#                     "two more, for specifying room permissions:\n" \
#                     "```" \
#                     ".makeprivate [-a admin...] [-r racer...]" \
#                     "```" \
#                     "Here `admin...` is a list of names of 'admins' for the race, which are users that can both see the race channel and " \
#                     "use special admin commands for managing the race, and `racer...` is a list of users that can see the race channel. " \
#                     "(Both admins and racers can enter the race, or not, as they prefer.)"
#         self._rm = race_module
#
#     def recognized_channel(self, channel):
#         return channel.is_private or channel == self._rm.main_channel
#
#     @asyncio.coroutine
#     def _do_execute(self, command):
#         race_private_info = raceprivateinfo.parse_args(command.args)
#         if race_private_info:
#             if not command.author.name in race_private_info.admin_names:
#                 race_private_info.admin_names.append(command.author.name)
#
#             try:
#                 yield from self._rm.make_private_race(race_private_info, creator=command.author)
# ##                race_channel = yield from self._rm.make_private_race(race_private_info, creator=command.author)
# ##                if race_channel:
# ##                    output_prestring = 'You have started a private race.'
# ##                    asyncio.ensure_future(self._rm.client.send_message(command.author,
# ##                        '{0}\nFormat: {2}\nChannel: {1}'.format(output_prestring, race_channel.mention, race_private_info.race_info.format_str())))
#             except discord.HTTPException as e:
#                 asyncio.ensure_future(self._rm.client.send_message(command.channel,
#                     'Error making race.'))
#                 logging.getLogger('discord').warning(e.response)