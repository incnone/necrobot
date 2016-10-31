from .botchannel import BotChannel
from ..command import admin, daily, prefs, racemake, seedgen


class PMBotChannel(BotChannel):
    def __init__(self, necrobot):
        BotChannel.__init__(self, necrobot)
        self.command_types = [
            admin.Die(self),
            admin.Help(self),
            admin.Info(self),
            admin.Register(self),
            admin.RegisterAll(self),
            daily.DailyChar(necrobot.daily_manager),
            daily.DailyResubmit(necrobot.daily_manager),
            daily.DailyRules(necrobot.daily_manager),
            daily.DailySchedule(necrobot.daily_manager),
            daily.DailySeed(necrobot.daily_manager),
            daily.DailyStatus(necrobot.daily_manager),
            daily.DailySubmit(necrobot.daily_manager),
            daily.DailyUnsubmit(necrobot.daily_manager),
            daily.DailyWhen(necrobot.daily_manager),
            daily.ForceRunNewDaily(necrobot.daily_manager),
            daily.ForceUpdateLeaderboard(necrobot.daily_manager),
            prefs.DailyAlert(self),
            prefs.RaceAlert(self),
            prefs.ViewPrefs(self),
            racemake.MakePrivate(self),
            seedgen.RandomSeed(self),
        ]
