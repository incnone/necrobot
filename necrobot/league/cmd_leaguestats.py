import necrobot.exception
from necrobot.botbase.commandtype import CommandType
from necrobot.league import leaguestats
from necrobot.league.leaguemgr import LeagueMgr
from necrobot.user import userlib
from necrobot.util import strutil


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
#             await {matches}send_message(
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


class LeagueFastest(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'fastest')
        self.help_text = 'Get fastest wins. Usage is `{} league_tag`.'.format(self.mention)

    async def _do_execute(self, cmd):
        if len(cmd.args) != 1:
            await cmd.channel.send(
                'Wrong number of arguments for `{}`. (Remember to specify the league.)'.format(self.mention)
            )
            return

        league_tag = cmd.args[0]
        try:
            await LeagueMgr().get_league(league_tag=league_tag)
        except necrobot.exception.LeagueDoesNotExist:
            await cmd.channel.send('Error: Can\'t find the league `{}`.'.format(league_tag))
            return

        infotext = await leaguestats.get_fastest_times_league_infotext(league_tag=league_tag, limit=20)
        infobox = '```\nFastest wins:\n{0}```'.format(
            strutil.tickless(infotext)
        )

        await cmd.channel.send(infobox)


class LeagueStats(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'stats')
        self.help_text = 'Get user stats. Usage is `{} league_tag "user_name"`.'.format(self.mention)

    async def _do_execute(self, cmd):
        if len(cmd.args) == 0:
            await cmd.channel.send('Please specify a league for `{}`.'.format(self.mention))
            return

        if len(cmd.args) > 2:
            await cmd.channel.send(
                'Too many arguments for `{}`. (Please enclose user names with spaces in quotes.)'
                .format(self.mention)
            )
            return

        league_tag = cmd.args[0]
        try:
            await LeagueMgr().get_league(league_tag=league_tag)
        except necrobot.exception.LeagueDoesNotExist:
            await cmd.channel.send('Error: Can\'t find the league `{}`.'.format(league_tag))
            return

        if len(cmd.args) == 1:
            user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)
        else:
            username = cmd.args[1]
            user = await userlib.get_user(any_name=username)
            if user is None:
                await cmd.channel.send(
                    "Couldn't find the user `{0}`.".format(username)
                )
                return

        stats = await leaguestats.get_league_stats(league_tag, user.user_id)
        infobox = '```\nStats: {username}\n{stats}\n```'\
                  .format(
                      username=strutil.tickless(user.display_name),
                      stats=strutil.tickless(stats.infotext)
                  )
        await cmd.channel.send(infobox)
