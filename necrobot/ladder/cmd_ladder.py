from necrobot.botbase.command import CommandType
from necrobot.race.match import matchutil
from necrobot.user import userutil


# General commands
class LadderRegister(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'ladderregister')
        self.help_text = 'Begin registering yourself for the Necrobot ladder.'

    async def _do_execute(self, cmd):
        await self.client.send_message(
            cmd.channel,
            '{0}: Registering doesn\'t do anything right now, but if it did, you\'d have done '
            'it.'.format(cmd.author.mention))
        pass


class NextRace(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'next')
        self.help_text = 'Displays upcoming ladder matches.'

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            cmd.channel,
            'This command is TODO.')
        pass


class Ranked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'ranked')
        self.help_text = 'Suggest a ranked ladder match with an opponent with `{0} opponent_name`. Both ' \
                         'players must do this for the match to be made.'.format(self.mention)

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            cmd.channel,
            'This command is TODO.')


class Unranked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'unranked')
        self.help_text = 'Suggest an unranked match with an opponent with `{0} opponent_name`. Both ' \
                         'players must do this for the match to be made.'.format(self.mention)

    async def _do_execute(self, cmd):
        # TODO
        await self.client.send_message(
            cmd.channel,
            'This command is TODO.')


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

        racer_names = (cmd.args[0], cmd.args[1])
        racers = []

        # Find the two racers
        for i in [0, 1]:
            racer_name = racer_names[i]
            try:
                racer = userutil.get_user(self.necrobot, discord_name=racer_name)
                if racer is None:
                    await self.client.send_message(
                        cmd.channel,
                        'Error: Could not find user with name `{0}`.'.format(racer_name))
                    return
                racers.append(racer)
            except userutil.DuplicateUserException:
                await self.client.send_message(
                    cmd.channel,
                    'Error: More than one user found with name `{0}`.'.format(racer_name))
                return

        # Create the Match object
        new_match = matchutil.make_registered_match(racer_1_id=racers[0].user_id, racer_2_id=racers[1].user_id)

        # Create the match room
        match_room = await matchutil.make_match_room(new_match)

        # Output success
        await self.client.send_message(
            cmd.channel,
            'Match created in channel {0}.'.format(
                match_room.channel.mention))
