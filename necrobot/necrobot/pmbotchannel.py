from necrobot.botbase import cmd_admin
from necrobot.botbase.botchannel import BotChannel
from necrobot.daily import cmd_daily
from necrobot.necrobot import cmd_seedgen
from necrobot.race import cmd_racemake
from necrobot.stats import cmd_stats
from necrobot.user import cmd_user


class PMBotChannel(BotChannel):
    def __init__(self):
        BotChannel.__init__(self)
        self.command_types = [
            cmd_admin.Die(self),
            cmd_admin.Help(self),
            cmd_admin.Info(self),
            cmd_admin.Reboot(self),

            cmd_daily.DailyChar(self),
            cmd_daily.DailyResubmit(self),
            cmd_daily.DailyRules(self),
            cmd_daily.DailySchedule(self),
            cmd_daily.DailySeed(self),
            cmd_daily.DailyStatus(self),
            cmd_daily.DailySubmit(self),
            cmd_daily.DailyUnsubmit(self),
            cmd_daily.DailyWhen(self),
            cmd_daily.ForceRunNewDaily(self),
            cmd_daily.ForceUpdateLeaderboard(self),

            cmd_user.DailyAlert(self),
            cmd_user.RaceAlert(self),
            cmd_user.Register(self),
            cmd_user.RegisterAll(self),
            cmd_user.ViewPrefs(self),

            cmd_racemake.Make(self),
            cmd_racemake.MakeCondor(self),
            cmd_racemake.MakePrivate(self),

            cmd_seedgen.RandomSeed(self),

            cmd_stats.Fastest(self),
            cmd_stats.MostRaces(self),
            cmd_stats.Stats(self),
        ]
