from necrobot.database import leaguedb, ratingsdb
from necrobot.match import cmd_match
from necrobot.user import userlib

from necrobot.config import Config
from necrobot.botbase.commandtype import CommandType
from necrobot.match.matchinfo import MatchInfo


# General commands
class LadderDrop(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'dropcurrent')
        self.help_text = 'Drop out of all currently scheduled ladder matches.'

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            cmd.channel,
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class LadderRegister(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'register')
        self.help_text = 'Register yourself for the Necrobot ladder.'

    async def _do_execute(self, cmd):
        user = await userlib.get_user(discord_id=int(cmd.author.id))

        if await leaguedb.is_registered(user.user_id):
            await self.client.send_message(
                cmd.channel,
                '{0}: You are already registered for the ladder.'.format(cmd.author.mention)
            )
        else:
            await leaguedb.register_user(user.user_id)
            await self.client.send_message(
                cmd.channel,
                '{0} has registered for the ladder. '.format(cmd.author.mention)
            )


class LadderUnregister(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'unregister')
        self.help_text = 'Unregister for the ladder.'

    async def _do_execute(self, cmd):
        user = await userlib.get_user(discord_id=int(cmd.author.id))

        if await leaguedb.is_registered(user.user_id):
            await leaguedb.unregister_user(user.user_id)
            await self.client.send_message(
                cmd.channel,
                '{0}: You are no longer registered for the ladder.'.format(cmd.author.mention)
            )
        else:
            await self.client.send_message(
                cmd.channel,
                '{0}: You are not registered for the ladder.'.format(cmd.author.mention)
            )


class SetAutomatch(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'setautomatch')
        self.help_text = '`{0} n`: Tells the bot you want `n` automatches per week. (`n` must be between 0 and {1}.)'\
                         .format(self.mention, Config.AUTOMATCH_MAX_MATCHES)

    async def _do_execute(self, cmd):
        user = await userlib.get_user(discord_id=int(cmd.author.id))

        if not await leaguedb.is_registered(user.user_id):
            await self.client.send_message(
                cmd.channel,
                '{0}: You are not registered for the ladder. Please register with `.register`.'
                .format(cmd.author.mention)
            )
            return

        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                'Wrong number of arguments for `{0}`. Please specify a number of races per week.'.format(self.mention)
            )
            return

        try:
            num_matches = int(cmd.args[0])
        except ValueError:
            await self.client.send_message(
                cmd.channel,
                'Error: Could\'t parse {0} as a number.'.format(cmd.args[0])
            )
            return

        if not (0 <= num_matches <= Config.AUTOMATCH_MAX_MATCHES):
            await self.client.send_message(
                cmd.channel,
                'Error: Number of automatches per week must be between 0 and {0}.'.format(Config.AUTOMATCH_MAX_MATCHES)
            )
            return

        await leaguedb.set_automatches(user.user_id, num_matches)
        await self.client.send_message(
            cmd.channel,
            '{auth}: You\'re now requesting {num} {matches} per week.'
            .format(
                auth=cmd.author.mention,
                num=num_matches,
                matches='match' if num_matches == 1 else 'matches'
            )
        )


class Ranked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'ranked')
        self.help_text = 'Create a ranked ladder match (`{0} opponent_name`).'.format(self.mention)

    @property
    def short_help_text(self):
        return 'Create ranked ladder match.'

    async def _do_execute(self, cmd):
        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                'Wrong number of arguments for `{0}`. '
                '(Enclose racer names with spaces inside quotes.)'.format(self.mention)
            )
            return

        await cmd_match.make_match_from_cmd(
            cmd=cmd,
            cmd_type=self,
            racer_members=[cmd.author],
            racer_names=[cmd.args[0]],
            match_info=MatchInfo(ranked=True)
        )


class Rating(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'rating')
        self.help_text = '`{} username` returns the rating of the discord user `username` (or your own by default).'\
                         .format(self.mention)

    @property
    def short_help_text(self):
        return 'Get ladder rating.'

    async def _do_execute(self, cmd):
        if len(cmd.args) == 0:
            user = await userlib.get_user(discord_id=int(cmd.author.id))
        elif len(cmd.args) == 1:
            user = await userlib.get_user(any_name=cmd.args[0])
            if user is None:
                await self.client.send_message(
                    cmd.channel,
                    'Couldn\'t find user {0}.'.format(cmd.args[0])
                )
                return
        else:
            await self.client.send_message(
                cmd.channel,
                'Error: Too many args for `{0}`. (Enclose names with spaces in quotes.)'.format(self.mention)
            )
            return

        rating = await ratingsdb.get_rating(user_id=user.user_id)
        await self.client.send_message(
            cmd.channel,
            '**{0}**: {1}'.format(user.display_name, rating.displayed_rating))


class Unranked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'unranked')
        self.help_text = 'Create an unranked ladder match (`{0} opponent_name`).'.format(self.mention)

    @property
    def short_help_text(self):
        return 'Create unranked match.'

    async def _do_execute(self, cmd):
        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                'Wrong number of arguments for `{0}`. '
                '(Enclose racer names with spaces inside quotes.)'.format(self.mention)
            )
            return

        await cmd_match.make_match_from_cmd(
            cmd=cmd,
            cmd_type=self,
            racer_members=[cmd.author],
            racer_names=[cmd.args[0]],
            match_info=MatchInfo(ranked=False)
        )


# Admin commands
class Automatch(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'automatch')
        self.help_text = 'Make automated ladder matches.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            cmd.channel,
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class CloseFinished(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'closefinished')
        self.help_text = 'Close all finished match rooms.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            cmd.channel,
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class DropRacer(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'dropracer')
        self.help_text = 'Drop a racer from all their current matches. ' \
                         'Usage is `{0} rtmp_name`.'.format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Drop a racer from current races.'

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            cmd.channel,
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class ForceRanked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-ranked')
        self.help_text = 'Create a ranked ladder match between two racers with ' \
                         '`{0} racer_1_name racer_2_name`.'.format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Create ranked ladder match.'

    async def _do_execute(self, cmd):
        # Parse arguments
        if len(cmd.args) != 2:
            await self.client.send_message(
                cmd.channel,
                'Error: Wrong number of arguments for `{0}`.'.format(self.mention))
            return

        await cmd_match.make_match_from_cmd(
            cmd=cmd,
            cmd_type=self,
            racer_names=[cmd.args[0], cmd.args[1]],
            match_info=MatchInfo(ranked=True)
        )
