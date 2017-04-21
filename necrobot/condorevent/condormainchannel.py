from necrobot.botbase import cmd_admin
from necrobot.race.match import cmd_match
from necrobot.stdconfig import cmd_seedgen
from necrobot.user import cmd_user
from necrobot.botbase.botchannel import BotChannel


class CondorMainChannel(BotChannel):
    def __init__(self):
        BotChannel.__init__(self)
        self.command_types = [
            cmd_admin.Help(self),
            cmd_admin.Info(self),

            # NextRace
            # StaffAlert

            cmd_match.Cawmentate(self),
            cmd_match.Uncawmentate(self),
            cmd_match.Vod(self),

            # cmd_stats.Fastest(self),
            # cmd_stats.MostRaces(self),
            # cmd_stats.Stats(self),

            cmd_user.Register(self),
            cmd_user.RTMP(self),
            cmd_user.SetInfo(self),
            cmd_user.Timezone(self),
            cmd_user.Twitch(self),
            cmd_user.UserInfo(self),
        ]
