from necrobot.botbase.command import CommandType


# General commands
class LadderRegister(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'ladderregister')
        self.help_text = 'Begin registering yourself for the Necrobot ladder.'

    async def _do_execute(self, cmd):
        pass


class NextRace(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'next')
        self.help_text = 'Displays upcoming ladder matches.'

    async def _do_execute(self, cmd):
        pass


class Ranked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'ranked')
        self.help_text = 'Suggest a ranked ladder match with an opponent with `.ranked opponent_name`. Both players ' \
                         'must do this for the match to be made.'

    async def _do_execute(self, cmd):
        pass


class Unranked(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'unranked')
        self.help_text = 'Suggest an unranked ladder match with an opponent with `.ranked opponent_name`. Both ' \
                         'players must do this for the match to be made.'

    async def _do_execute(self, cmd):
        pass
