from necrobot.botbase.botchannel import BotChannel
from necrobot.league import cmd_league
from necrobot.match import cmd_match
from necrobot.stats import cmd_stats
from necrobot.user import cmd_user


class CondorMainChannel(BotChannel):
    def __init__(self):
        BotChannel.__init__(self)
        self.channel_commands = [
            cmd_league.NextRace(self),

            cmd_match.Cawmentate(self),
            cmd_match.Uncawmentate(self),
            cmd_match.Vod(self),

            cmd_stats.LeagueFastest(self),
            cmd_stats.LeagueStats(self),

            cmd_user.RTMP(self),
            cmd_user.SetInfo(self),
            cmd_user.Timezone(self),
            cmd_user.Twitch(self),
            cmd_user.UserInfo(self),
        ]
