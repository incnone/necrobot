from necrobot.botbase.command import Command, CommandType
from necrobot.database import necrodb
from necrobot.race.match import matchutil
from necrobot.user import userutil


# General commands
class LadderRegister(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'ladderregister')
        self.help_text = 'Begin registering yourself for the Necrobot ladder.'

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            cmd.channel,
            '{0}: Registering doesn\'t do anything right now, but if it did, you\'d have done '
            'it.'.format(cmd.author.mention))


class NextRace(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'next')
        self.help_text = 'Displays upcoming ladder matches.'

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            cmd.channel,
            'This command is TODO.')


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
            necro_user = userutil.get_user(discord_name=cmd.args[0])
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

        rating = necrodb.get_rating(discord_id=discord_id)
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
        try:
            racer_as_necrouser = userutil.get_user(discord_name=name)
        except userutil.DuplicateUserException:
            await cmd_type.client.send_message(
                cmd.channel,
                'Error: More than one user found with name `{0}`.'.format(name))
            return

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
    new_match = matchutil.make_registered_match(
        racer_1_id=racers[0].user_id,
        racer_2_id=racers[1].user_id,
        ranked=ranked
    )

    # Create the match room
    match_room = await matchutil.make_match_room(new_match)

    # Output success
    await cmd_type.client.send_message(
        cmd.channel,
        'Match created in channel {0}.'.format(
            match_room.channel.mention))
