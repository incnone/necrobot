from necrobot.botbase import cmd_seedgen
from necrobot.botbase.botchannel import BotChannel
from necrobot.ladder import cmd_ladder
from necrobot.race import cmd_racestats
from necrobot.user import cmd_user


class LadderAdminChannel(BotChannel):
    def __init__(self):
        BotChannel.__init__(self)
        self.channel_commands = [
            cmd_ladder.Automatch(self),
            cmd_ladder.CloseFinished(self),
            cmd_ladder.DropRacer(self),
            cmd_ladder.ForceRanked(self),

            cmd_seedgen.RandomSeed(self),

            cmd_racestats.Fastest(self),
            cmd_racestats.MostRaces(self),
            cmd_racestats.Stats(self),

            cmd_user.RTMP(self),
            cmd_user.UserInfo(self),
        ]
