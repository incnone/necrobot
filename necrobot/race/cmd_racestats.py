from necrobot.botbase.commandtype import CommandType
from necrobot.race import racestats
from necrobot.user import userlib
from necrobot.util import server
from necrobot.util import strutil
from necrobot.util.necrodancer.character import NDChar


class Fastest(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'fastest')
        self.help_text = '`.fastest <character_name>` shows the fastest times for a given character. By ' \
                         'default this shows Amplified times. Use `.fastest <character_name> nodlc to get ' \
                         'base-game times.'

    async def _do_execute(self, cmd):
        await server.client.send_typing(cmd.channel)
        amplified = True

        # Parse arguments
        args = cmd.args
        try:
            base_arg_pos = args.index('nodlc')
            amplified = False
            args.pop(base_arg_pos)
        except ValueError:
            pass

        if len(cmd.args) != 1:
            await cmd.channel.send(
                '{0}: Wrong number of arguments for `.fastest`.'.format(cmd.author.mention))
            return

        ndchar = NDChar.fromstr(args[0])
        if ndchar is None:
            await cmd.channel.send(
                '{0}: Couldn\'t parse {1} as a character.'.format(cmd.author.mention, args[0]))
            return

        infotext = await racestats.get_fastest_times_infotext(ndchar, amplified, 20)
        infobox = 'Fastest public all-zones {2} {0} times:\n```\n{1}```'.format(
            ndchar.name,
            strutil.tickless(infotext),
            'Amplified' if amplified else 'base-game')
        await cmd.channel.send(infobox)


class MostRaces(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'mostraces')
        self.help_text = '`.mostraces <character_name>` shows the racers with the largest number of (public, ' \
                         'all-zones) races for that character.'

    async def _do_execute(self, cmd):
        if len(cmd.args) != 1:
            await cmd.channel.send(
                '{0}: Wrong number of arguments for `.mostraces`.'.format(cmd.author.mention))
            return

        ndchar = NDChar.fromstr(cmd.args[0])
        if ndchar is None:
            await cmd.channel.send(
                '{0}: Couldn\'t parse {1} as a character.'.format(cmd.author.mention, cmd.args[0]))
            return

        infotext = await racestats.get_most_races_infotext(ndchar, 20)
        infobox = 'Most public all-zones {0} races:\n```\n{1}```'.format(
            ndchar.name,
            strutil.tickless(infotext)
        )
        await cmd.channel.send(
            infobox
        )


class Stats(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'stats')
        self.help_text = 'Show your own race stats, or use `.stats <username>` to show for a different user. ' \
                         'By default this shows stats for Amplified races; to get stats for the base game, ' \
                         'call `.stats <username> nodlc`.'

    async def _do_execute(self, cmd):
        amplified = True

        # Parse arguments
        args = cmd.args
        try:
            base_arg_pos = args.index('nodlc')
            amplified = False
            args.pop(base_arg_pos)
        except ValueError:
            pass

        if len(args) > 1:
            await cmd.channel.send(
                '{0}: Error: wrong number of arguments for `.stats`.'.format(cmd.author.mention))
            return

        if len(args) == 0:
            user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)
        else:  # len(args) == 1
            racer_name = args[0]
            user = await userlib.get_user(any_name=racer_name)
            if user is None:
                await cmd.channel.send(
                    'Could not find user "{0}".'.format(racer_name))
                return

        # Show stats
        general_stats = await racestats.get_general_stats(user.user_id, amplified=amplified)
        await cmd.channel.send(
            '```\n{0}\'s stats ({1}, public all-zones races):\n{2}\n```'.format(
                strutil.tickless(user.display_name),
                'Amplified' if amplified else 'Base game',
                general_stats.infotext)
        )
