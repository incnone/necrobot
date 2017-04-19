from necrobot.botbase.botchannel import BotChannel
from necrobot.botbase import cmd_admin
from necrobot.ladder import cmd_ladder
from necrobot.stdconfig import cmd_seedgen
from necrobot.stats import cmd_stats
from necrobot.user import cmd_user


class LadderAdminChannel(BotChannel):
    def __init__(self):
        BotChannel.__init__(self)
        self.command_types = [
            cmd_admin.Help(self),
            cmd_admin.Info(self),

            cmd_ladder.Automatch(self),
            cmd_ladder.CloseFinished(self),
            cmd_ladder.DropRacer(self),
            cmd_ladder.ForceRanked(self),

            cmd_seedgen.RandomSeed(self),

            cmd_stats.Fastest(self),
            cmd_stats.MostRaces(self),
            cmd_stats.Stats(self),

            cmd_user.RTMP(self),
            cmd_user.UserInfo(self),
        ]
