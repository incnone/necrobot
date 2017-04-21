import necrobot.database.ladderdb
from necrobot.botbase.command import Command, CommandType
from necrobot.database import dbconnect
from necrobot.race.match import matchutil
from necrobot.user import userutil


# General commands
class LadderDropMyMatches(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'ladder-drop-my-matches')
        self.help_text = 'Drop out of all currently scheduled ladder matches.'

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class LadderFastest(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'ladder-fastest')
        self.help_text = 'Get a list of the fastest ranked ladder clears.'

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class LadderRegister(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'ladder-register')
        self.help_text = 'Begin registering yourself for the Necrobot ladder.'

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            cmd.channel,
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class LadderStats(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'ladder-stats')
        self.help_text = 'Display racer stats. Usage is `.stats rtmp_name`. If no racer is given, will display ' \
                         'stats for the command caller.'

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            cmd.channel,
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class NextRace(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'next')
        self.help_text = 'Displays upcoming ladder matches.'

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class Ranked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'ranked')
        self.help_text = 'Create a ranked ladder match (`{0} opponent_name`).'.format(self.mention)

    async def _do_execute(self, cmd):
        if len(cmd.args[0]) != 1:
            await self.client.send_message(
                cmd.channel,
                'Wrong number of arguments for `{0}`. '
                '(Enclose racer names with spaces inside quotes.)'.format(self.mention)
            )
            return

        await _create_match(
            cmd=cmd,
            cmd_type=self,
            racer_members=[cmd.author],
            racer_names=[cmd.args[0]],
            ranked=True
        )


class Rating(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'rating')
        self.help_text = '`{} username` returns the TrueSkill rating of the discord user `username`; if no ' \
                         'username is given, returns your TrueSkill rating.'

    async def _do_execute(self, cmd):
        if len(cmd.args) == 0:
            user_name = cmd.author.display_name
            discord_id = int(cmd.author.id)
        elif len(cmd.args) == 1:
            necro_user = userutil.get_user(any_name=cmd.args[0])
            if necro_user is None:
                await self.client.send_message(
                    cmd.channel,
                    'Couldn\'t find user {0}.'.format(cmd.args[0])
                )
                return
            user_name = necro_user.discord_name
            discord_id = necro_user.discord_id
        else:
            await self.client.send_message(
                cmd.channel,
                'Error: Too many args for `{0}`. (Enclose names with spaces in quotes.)'.format(self.mention)
            )
            return

        rating = necrobot.database.ladderdb.get_rating(discord_id=discord_id)
        await self.client.send_message(
            cmd.channel,
            '**{0}**: {1}'.format(user_name, rating.displayed_rating))


class Unranked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'unranked')
        self.help_text = 'Suggest an unranked match with an opponent with `{0} opponent_name`. Both ' \
                         'players must do this for the match to be made.'.format(self.mention)

    async def _do_execute(self, cmd):
        if len(cmd.args[0]) != 1:
            await self.client.send_message(
                cmd.channel,
                'Wrong number of arguments for `{0}`. '
                '(Enclose racer names with spaces inside quotes.)'.format(self.mention)
            )
            return

        await _create_match(
            cmd=cmd,
            cmd_type=self,
            racer_members=[cmd.author],
            racer_names=[cmd.args[0]],
            ranked=False
        )


# Admin commands
class Automatch(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'automatch')
        self.help_text = '[Admin only] Make the automated ladder matches.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class CloseFinished(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'closefinished')
        self.help_text = '[Admin only] Close all finished match rooms.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class DropRacer(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'dropracer')
        self.help_text = '[Admin only] Drop a racer from all their current matches. ' \
                         'Usage is `{0} rtmp_name`.'.format(self.mention)
        self.admin_only = True

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            '`{0}` doesn\'t do anything yet, but if it did, you\'d be doing it.'.format(self.mention)
        )


class ForceRanked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-ranked')
        self.help_text = '[Admin only] Create a ranked ladder match between two racers with ' \
                         '`{0} racer_1_name racer_2_name`.'.format(self.mention)
        self.admin_only = True

    async def _do_execute(self, cmd):
        # Parse arguments
        if len(cmd.args) != 2:
            await self.client.send_message(
                cmd.channel,
                'Error: Wrong number of arguments for `{0}`.'.format(self.mention))
            return

        await _create_match(
            cmd=cmd,
            cmd_type=self,
            racer_names=[cmd.args[0], cmd.args[1]],
            ranked=True
        )


async def _create_match(
        cmd: Command,
        cmd_type: CommandType,
        racer_members=list(),
        racer_names=list(),
        ranked=False
):
    racers = []

    # Add the racers from member objects
    for member in racer_members:
        racer_as_necrouser = userutil.get_user(discord_id=member.id)
        if racer_as_necrouser is not None:
            racers.append(racer_as_necrouser)
        else:
            await cmd_type.client.send_message(
                cmd.channel,
                'Unexpected error: Couldn\'t find `{0}` in the database.'.format(member.display_name)
            )
            return

    # Add the racers from names
    for name in racer_names:
        racer_as_necrouser = userutil.get_user(any_name=name)

        if racer_as_necrouser is not None:
            racers.append(racer_as_necrouser)
        else:
            await cmd_type.client.send_message(
                cmd.channel,
                'Couldn\'t find a user with name `{0}`.'.format(name)
            )
            return

    # Check we have exactly two racers
    if len(racers) != 2:
        await cmd_type.client.send_message(
            cmd.channel,
            'Unexpected error: Tried to create a match with more than two racers.'
        )
        return

    # Create the Match object
    new_match = matchutil.make_match(
        racer_1_id=racers[0].user_id,
        racer_2_id=racers[1].user_id,
        ranked=ranked,
        register=True
    )

    # Create the match room
    match_room = await matchutil.make_match_room(new_match)

    # Output success
    await cmd_type.client.send_message(
        cmd.channel,
        'Match created in channel {0}.'.format(
            match_room.channel.mention))
