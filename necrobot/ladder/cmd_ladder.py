from necrobot.botbase.command import CommandType


# General commands
class LadderRegister(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'ladderregister')
        self.help_text = 'Begin registering yourself for the Necrobot ladder.'

    async def _do_execute(self, cmd):
        await self.necrobot.client.write(
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
        await self.necrobot.client.write(
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
        await self.necrobot.client.write(
            cmd.channel,
            'This command is TODO.')
        pass


class Unranked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'unranked')
        self.help_text = 'Suggest an unranked match with an opponent with `{0} opponent_name`. Both ' \
                         'players must do this for the match to be made.'.format(self.mention)

    async def _do_execute(self, cmd):
        # TODO
        await self.necrobot.client.write(
            cmd.channel,
            'This command is TODO.')
        pass


# Admin commands
class ForceRanked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-ranked')
        self.help_text = '[Admin only] Create a ranked ladder match between two racers with ' \
                         '`{0} racer_1_name racer_2_name`.'.format(self.mention)
        self.admin_only = True

    async def _do_execute(self, cmd):
        # TODO
        await self.necrobot.client.write(
            cmd.channel,
            'This command is TODO.')
        pass
