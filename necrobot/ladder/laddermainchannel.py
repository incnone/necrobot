from necrobot.botbase.botchannel import BotChannel
from necrobot.ladder import cmd_ladder
from necrobot.league import cmd_league
from necrobot.league import cmd_leaguestats
from necrobot.user import cmd_user


class LadderMainChannel(BotChannel):
    def __init__(self):
        BotChannel.__init__(self)
        self.channel_commands = [
            # cmd_ladder.LadderLeaderboard(self),
            cmd_ladder.Ranked(self),
            cmd_ladder.Rating(self),
            # cmd_ladder.SetAutomatch(self),
            cmd_ladder.Unranked(self),

            cmd_league.NextRace(self),

            cmd_league.Cawmentate(self),
            cmd_league.Uncawmentate(self),

            cmd_leaguestats.LeagueFastest(self),
            cmd_leaguestats.LeagueStats(self),

            cmd_user.SetInfo(self),
            cmd_user.Timezone(self),
            cmd_user.Twitch(self),
            cmd_user.UserInfo(self),
        ]
