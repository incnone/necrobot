from necrobot.botbase import cmd_admin
from necrobot.league import cmd_leaguestats
from necrobot.match import cmd_match
from necrobot.user import cmd_user

from necrobot.botbase.botchannel import BotChannel


class CondorPMChannel(BotChannel):
    def __init__(self):
        BotChannel.__init__(self)
        self.channel_commands = [
            cmd_admin.Die(self),
            cmd_admin.RaiseException(self),
            cmd_admin.Reboot(self),
            cmd_admin.RedoInit(self),

            cmd_match.Vod(self),

            cmd_leaguestats.LeagueFastest(self),
            cmd_leaguestats.LeagueStats(self),

            cmd_user.RTMP(self),
            cmd_user.SetInfo(self),
            cmd_user.Timezone(self),
            cmd_user.Twitch(self),
            cmd_user.UserInfo(self),
        ]
