from necrobot.botbase.botchannel import BotChannel
from necrobot.ladder import cmd_ladder
from necrobot.league import cmd_league
from necrobot.test import cmd_test
from necrobot.user import cmd_user


class LadderAdminChannel(BotChannel):
    def __init__(self):
        BotChannel.__init__(self)
        self.channel_commands = [
            cmd_ladder.Automatch(self),
            cmd_ladder.CloseFinished(self),
            cmd_ladder.ComputeRatings(self),
            cmd_ladder.DropRacer(self),
            cmd_ladder.ForceRanked(self),

            cmd_league.RegisterLadder(self),

            cmd_test.TestRate(self),

            cmd_user.RTMP(self),
            cmd_user.UserInfo(self),
        ]
