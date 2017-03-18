from .botchannel import BotChannel
from ..command import admin, color, daily, prefs, racemake, seedgen


class MainBotChannel(BotChannel):
    def __init__(self, necrobot):
        BotChannel.__init__(self, necrobot)
        self.command_types = [
            admin.Die(self),
            admin.Help(self),
            admin.Info(self),
            admin.Reboot(self),
            admin.Register(self),
            admin.RedoInit(self),
            color.ColorMe(self),
            daily.DailyChar(self),
            daily.DailyRules(self),
            daily.DailySchedule(self),
            daily.DailySeed(self),
            daily.DailyWhen(self),
            prefs.DailyAlert(self),
            prefs.RaceAlert(self),
            prefs.ViewPrefs(self),
            racemake.Make(self),
            racemake.MakeCondor(self),
            racemake.MakePrivate(self),
            seedgen.RandomSeed(self),
        ]
