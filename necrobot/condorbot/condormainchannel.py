from necrobot.botbase import cmd_admin
from necrobot.league import cmd_league
from necrobot.league import cmd_leaguestats
# from necrobot.speedrun import cmd_speedrun
from necrobot.user import cmd_user

from necrobot.botbase.botchannel import BotChannel


class CondorMainChannel(BotChannel):
    def __init__(self, ladder=False):
        BotChannel.__init__(self)

        self.channel_commands = [
            cmd_admin.Die(self),
            cmd_admin.RedoInit(self),

            cmd_league.NextRace(self),

            cmd_league.Cawmentate(self),
            cmd_league.Uncawmentate(self),

            cmd_leaguestats.LeagueFastest(self),
            cmd_leaguestats.LeagueStats(self),

            # cmd_speedrun.Submit(self),

            cmd_user.RTMP(self),
            cmd_user.SetInfo(self),
            cmd_user.SetPronouns(self),
            cmd_user.Timezone(self),
            cmd_user.Twitch(self),
            cmd_user.UserInfo(self),
        ]

        if ladder:
            self.channel_commands.append(cmd_league.MakeMatch(self))
