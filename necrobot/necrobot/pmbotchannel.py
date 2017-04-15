from necrobot.botbase.botchannel import BotChannel
from necrobot.necrobot import cmdseedgen, cmdadmin
from necrobot.daily import command
from necrobot.prefs import command
from necrobot.race import makecommand
from necrobot.stats import command


class PMBotChannel(BotChannel):
    def __init__(self, necrobot):
        BotChannel.__init__(self, necrobot)
        self.command_types = [
            cmdadmin.Die(self),
            cmdadmin.Help(self),
            cmdadmin.Info(self),
            cmdadmin.Reboot(self),
            cmdadmin.Register(self),
            cmdadmin.RegisterAll(self),
            command.DailyChar(self),
            command.DailyResubmit(self),
            command.DailyRules(self),
            command.DailySchedule(self),
            command.DailySeed(self),
            command.DailyStatus(self),
            command.DailySubmit(self),
            command.DailyUnsubmit(self),
            command.DailyWhen(self),
            command.ForceRunNewDaily(self),
            command.ForceUpdateLeaderboard(self),
            command.DailyAlert(self),
            command.RaceAlert(self),
            command.ViewPrefs(self),
            makecommand.Make(self),
            makecommand.MakeCondor(self),
            makecommand.MakePrivate(self),
            cmdseedgen.RandomSeed(self),
            # stats.Matchup(self),
            command.Fastest(self),
            command.MostRaces(self),
            command.Stats(self),
        ]
