from necrobot.database import userdb
from necrobot.stats import statfn

from necrobot.botbase.commandtype import CommandType
from necrobot.util.character import NDChar


# class Matchup(CommandType):
#     def __init__(self, bot_channel):
#         CommandType.__init__(self, bot_channel, 'matchup')
#         self.help_text = '`.matchup charname [-base] racer_1 racer_2`: Get an estimate of the matchup between ' \
#                          'racer_1 and racer_2 on the character charname. `-base` looks at base game stats; ' \
#                          'otherwise Amplified is used by default.'
#
#     async def _do_execute(self, cmd):
#         await self.necrobot.client.send_typing(cmd.necrobot)
#
#         amplified = True
#         args = cmd.args
#         try:
#             base_arg_pos = args.index('-base')
#             amplified = False
#             args.pop(base_arg_pos)
#         except ValueError:
#             pass
#
#         if len(args) != 3:
#             await self.client.send_message(
#                 cmd.necrobot,
#                 '{0}: Error: Wrong number of arguments for `.matchup`.'.format(cmd.author.mention))
#             return
#
#         ndchar = character.get_char_from_str(args[0])
#         if ndchar is None:
#             await self.client.send_message(
#                 cmd.necrobot,
#                 '{0}: Error: Can\'t parse {1} as a character name.'.format(cmd.author.mention, args[0]))
#             return
#
#         member_1 = self.necrobot.find_member(args[1])
#         if member_1 is None:
#             await self.client.send_message(
#                 cmd.necrobot,
#                 '{0}: Error: Can\'t find user {1}.'.format(cmd.author.mention, args[1]))
#             return
#
#         member_2 = self.necrobot.find_member(args[2])
#         if member_2 is None:
#             await self.client.send_message(
#                 cmd.necrobot,
#                 '{0}: Error: Can\'t find user {1}.'.format(cmd.author.mention, args[2]))
#             return
#
#         win_data = statfn.get_winrates(int(member_1.id), int(member_2.id), ndchar, amplified)
#         if win_data is None:
#             await self.client.send_message(
#                 cmd.necrobot,
#                 '{0}: Error: At least one of these racers doesn\'t have enough wins to do this prediction.'.format(
#                     cmd.author.mention))
#             return
#
#         await self.client.send_message(
#             cmd.necrobot,
#             'Predicted outcome: **{0}** [{1}% - {2}%] **{3}** ({4}% chance of neither finishing).'.format(
#                 member_1.display_name,
#                 int(win_data[0]*100),
#                 int(win_data[1]*100),
#                 member_2.display_name,
#                 int(win_data[2]*100)))


class Fastest(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'fastest')
        self.help_text = '`.fastest <character_name>` shows the fastest times for a given character. By ' \
                         'default this shows Amplified times. Use `.fastest <character_name> -base to get ' \
                         'base-game times.'

    async def _do_execute(self, cmd):
        await self.necrobot.client.send_typing(cmd.channel)
        amplified = True

        # Parse arguments
        args = cmd.args
        try:
            base_arg_pos = args.index('-base')
            amplified = False
            args.pop(base_arg_pos)
        except ValueError:
            pass

        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                '{0}: Wrong number of arguments for `.fastest`.'.format(cmd.author.mention))
            return

        ndchar = NDChar.fromstr(args[0])
        if ndchar is None:
            await self.client.send_message(
                cmd.channel,
                '{0}: Couldn\'t parse {1} as a character.'.format(cmd.author.mention, args[0]))
            return

        infobox = 'Fastest public all-zones {2} {0} times:\n```\n{1}```'.format(
            ndchar.name,
            statfn.get_fastest_times_infotext(ndchar, amplified, 20),
            'Amplified' if amplified else 'base-game')
        await self.client.send_message(
            cmd.channel,
            infobox)


# class LeagueFastest(CommandType):
#     def __init__(self, bot_channel):
#         CommandType.__init__(self, bot_channel, 'fastest')
#         self.help_text = 'Get fastest wins.'
#
#     async def _do_execute(self, cmd):
#         infobox = '```\nFastest wins:\n{0}```'.format(
#             statfn.get_fastest_times_infotext(NDChar.Cadence, True, 20)
#         )
#
#         await self.client.send_message(cmd.channel, infobox)


class MostRaces(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'mostraces')
        self.help_text = '`.mostraces <character_name>` shows the racers with the largest number of (public, ' \
                         'all-zones) races for that character.'

    async def _do_execute(self, cmd):
        await self.necrobot.client.send_typing(cmd.channel)
        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                '{0}: Wrong number of arguments for `.mostraces`.'.format(cmd.author.mention))
            return

        ndchar = NDChar.fromstr(cmd.args[0])
        if ndchar is None:
            await self.client.send_message(
                cmd.channel,
                '{0}: Couldn\'t parse {1} as a character.'.format(cmd.author.mention, cmd.args[0]))
            return

        infobox = 'Most completed public all-zones {0} races:\n```\n{1}```'.format(
            ndchar.name,
            statfn.get_most_races_infotext(ndchar, 20))
        await self.client.send_message(
            cmd.channel,
            infobox)


class Stats(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'stats')
        self.help_text = 'Show your own race stats, or use `.stats <username>` to show for a different user. By ' \
                         'default this shows stats for Amplified races; to get stats for the base game, call ' \
                         '`.stats <username> -base`.'

    async def _do_execute(self, cmd):
        await self.necrobot.client.send_typing(cmd.channel)

        amplified = True

        # Parse arguments
        args = cmd.args
        try:
            base_arg_pos = args.index('-base')
            amplified = False
            args.pop(base_arg_pos)
        except ValueError:
            pass

        if len(args) > 1:
            await self.client.send_message(
                cmd.channel,
                '{0}: Error: wrong number of arguments for `.stats`.'.format(cmd.author.mention))
            return

        racer_name = cmd.author.display_name
        racer_id = int(cmd.author.id)
        if len(args) == 1:
            racer_name = args[0]
            member = self.necrobot.find_member(discord_name=racer_name)
            if member is not None:
                racer_name = member.display_name
                racer_id = int(member.id)
            else:
                racer_id = int(userdb.get_discord_id(racer_name))
                if racer_id is None:
                    await self.client.send_message(
                        cmd.channel,
                        '{0}: Could not find user "{1}".'.format(cmd.author.mention, args[0]))
                    return

        # Show stats
        general_stats = statfn.get_general_stats(racer_id, amplified=amplified)
        await self.client.send_message(
            cmd.channel,
            '```\n{0}\'s stats ({1}, public all-zones races):\n{2}\n```'.format(
                racer_name,
                'Amplified' if amplified else 'Base game',
                general_stats.infotext))
