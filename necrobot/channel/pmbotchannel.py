from .botchannel import BotChannel
from ..command import admin
# from ..command import racemake
from ..command import seedgen


class PMBotChannel(BotChannel):
    def __init__(self, necrobot):
        BotChannel.__init__(self, necrobot)
        self.command_types = [
            admin.Die(self),
            admin.Help(self),
            admin.Register(self),
            admin.RegisterAll(self),
            # racemake.MakePrivate(self),
            seedgen.RandomSeed(self),
        ]
