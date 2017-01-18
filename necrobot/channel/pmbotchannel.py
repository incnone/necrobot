from .botchannel import BotChannel
from ..command import admin, daily, prefs, racemake, seedgen


class PMBotChannel(BotChannel):
    def __init__(self, necrobot):
        BotChannel.__init__(self, necrobot)
        self.command_types = [
            admin.Die(self),
            admin.Help(self),
            admin.Info(self),
            admin.Reboot(self),
            admin.Register(self),
            admin.RegisterAll(self),
            daily.DailyChar(self),
            daily.DailyResubmit(self),
            daily.DailyRules(self),
            daily.DailySchedule(self),
            daily.DailySeed(self),
            daily.DailyStatus(self),
            daily.DailySubmit(self),
            daily.DailyUnsubmit(self),
            daily.DailyWhen(self),
            daily.ForceRunNewDaily(self),
            daily.ForceUpdateLeaderboard(self),
            prefs.DailyAlert(self),
            prefs.RaceAlert(self),
            prefs.ViewPrefs(self),
            racemake.MakePrivate(self),
            seedgen.RandomSeed(self),
        ]
