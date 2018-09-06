from necrobot.botbase.commandtype import CommandType
from necrobot.stats import statfn
from necrobot.user import userlib
from necrobot.util import server
from necrobot.util import strutil
from necrobot.util.necrodancer.character import NDChar


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
#         member_1 = server.find_member(args[1])
#         if member_1 is None:
#             await self.client.send_message(
#                 cmd.necrobot,
#                 '{0}: Error: Can\'t find user {1}.'.format(cmd.author.mention, args[1]))
#             return
#
#         member_2 = server.find_member(args[2])
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
        await server.client.send_typing(cmd.channel)
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

        infotext = await statfn.get_fastest_times_infotext(ndchar, amplified, 20)
        infobox = 'Fastest public all-zones {2} {0} times:\n```\n{1}```'.format(
            ndchar.name,
            strutil.tickless(infotext),
            'Amplified' if amplified else 'base-game')
        await self.client.send_message(
            cmd.channel,
            infobox)


class LeagueFastest(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'fastest')
        self.help_text = 'Get fastest wins.'

    async def _do_execute(self, cmd):
        infotext = await statfn.get_fastest_times_league_infotext(20)
        infobox = '```\nFastest wins:\n{0}```'.format(
            strutil.tickless(infotext)
        )

        await self.client.send_message(cmd.channel, infobox)


class LeagueStats(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'stats')
        self.help_text = 'Get user stats.'

    async def _do_execute(self, cmd):
        if len(cmd.args) == 0:
            user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)
        else:
            username = cmd.arg_string
            user = await userlib.get_user(any_name=username)
            if user is None:
                await self.client.send_message(
                    cmd.channel,
                    "Couldn't find the user `{0}`.".format(username)
                )
                return

        stats = await statfn.get_league_stats(user.user_id)
        infobox = '```\nStats: {username}\n{stats}\n```'\
                  .format(
                      username=strutil.tickless(user.display_name),
                      stats=strutil.tickless(stats.infotext)
                  )
        await self.client.send_message(cmd.channel, infobox)


class MostRaces(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'mostraces')
        self.help_text = '`.mostraces <character_name>` shows the racers with the largest number of (public, ' \
                         'all-zones) races for that character.'

    async def _do_execute(self, cmd):
        await server.client.send_typing(cmd.channel)
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

        infotext = await statfn.get_most_races_infotext(ndchar, 20)
        infobox = 'Most public all-zones {0} races:\n```\n{1}```'.format(
            ndchar.name,
            strutil.tickless(infotext)
        )
        await self.client.send_message(
            cmd.channel,
            infobox
        )


class Stats(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'stats')
        self.help_text = 'Show your own race stats, or use `.stats <username>` to show for a different user. By ' \
                         'default this shows stats for Amplified races; to get stats for the base game, call ' \
                         '`.stats <username> -base`.'

    async def _do_execute(self, cmd):
        await server.client.send_typing(cmd.channel)

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

        if len(args) == 0:
            user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)
        else:  # len(args) == 1
            racer_name = args[0]
            user = await userlib.get_user(any_name=racer_name)
            if user is None:
                await self.client.send_message(
                    cmd.channel,
                    'Could not find user "{0}".'.format(racer_name))
                return

        # Show stats
        general_stats = await statfn.get_general_stats(user.user_id, amplified=amplified)
        await self.client.send_message(
            cmd.channel,
            '```\n{0}\'s stats ({1}, public all-zones races):\n{2}\n```'.format(
                strutil.tickless(user.display_name),
                'Amplified' if amplified else 'Base game',
                general_stats.infotext)
        )
