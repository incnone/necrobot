from necrobot.ladder import ratingsdb
from necrobot.botbase.commandtype import CommandType
from necrobot.match.matchinfo import MatchInfo
from necrobot.user import userlib


# General commands
class LadderLeaderboard(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'leaderboard')
        self.help_text = 'View the current ladder leaderboard.'

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            cmd.channel,
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class SetAutomatch(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'setautomatch')
        self.help_text = '`{} n`: Tell the bot you want `n` automatically generated matches per week.' \
                         .format(self.mention)

    @property
    def short_help_text(self):
        return 'Set number of desired matchups per week.'

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            cmd.channel,
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class Ranked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'ranked')
        self.help_text = 'Create a ranked ladder match (`{} opponent_name`).'.format(self.mention)

    @property
    def short_help_text(self):
        return 'Create ladder match.'

    async def _do_execute(self, cmd):
        if len(cmd.args[0]) != 1:
            await self.client.send_message(
                cmd.channel,
                'Wrong number of arguments for `{}`. (Enclose racer names with spaces inside quotes.)'
                .format(self.mention)
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
        self.help_text = '`{} username` returns the TrueSkill rating of the discord user `username`; if no ' \
                         'username is given, returns your TrueSkill rating.'.format(self.mention)

    @property
    def short_help_text(self):
        return 'Get ladder rating.'

    async def _do_execute(self, cmd):
        if len(cmd.args) == 0:
            user_name = cmd.author.display_name
            discord_id = int(cmd.author.id)
        elif len(cmd.args) == 1:
            necro_user = await userlib.get_user(any_name=cmd.args[0])
            if necro_user is None:
                await self.client.send_message(
                    cmd.channel,
                    'Couldn\'t find user {}.'.format(cmd.args[0])
                )
                return
            user_name = necro_user.display_name
            discord_id = necro_user.discord_id
        else:
            await self.client.send_message(
                cmd.channel,
                'Error: Too many args for `{}`. (Enclose names with spaces in quotes.)'.format(self.mention)
            )
            return

        rating = await ratingsdb.get_rating(discord_id=discord_id)
        await self.client.send_message(
            cmd.channel,
            '**{0}**: {1}'.format(user_name, rating.displayed_rating))


class Unranked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'unranked')
        self.help_text = 'Suggest an unranked match with an opponent with `{} opponent_name`. Both ' \
                         'players must do this for the match to be made.'.format(self.mention)

    @property
    def short_help_text(self):
        return 'Create unranked match.'

    async def _do_execute(self, cmd):
        if len(cmd.args[0]) != 1:
            await self.client.send_message(
                cmd.channel,
                'Wrong number of arguments for `{}`. (Enclose racer names with spaces inside quotes.)'
                .format(self.mention)
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
            '`{}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
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
            '`{}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
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
                'Error: Wrong number of arguments for `{}`.'.format(self.mention))
            return

        await cmd_match.make_match_from_cmd(
            cmd=cmd,
            cmd_type=self,
            racer_names=[cmd.args[0], cmd.args[1]],
            match_info=MatchInfo(ranked=True)
        )
