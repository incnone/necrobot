from .botchannel import BotChannel
from ..command import admin
from ..command import color
from ..command import racemake
from ..command import seedgen


class MainBotChannel(BotChannel):
    def __init__(self, necrobot):
        BotChannel.__init__(self, necrobot)
        self.command_types = [
            admin.Die(self),
            admin.Help(self),
            admin.Info(self),
            admin.Register(self),
            admin.RegisterAll(self),
            color.ColorMe(self),
            racemake.Make(self),
            # racemake.MakePrivate(self),
            seedgen.RandomSeed(self),
        ]
