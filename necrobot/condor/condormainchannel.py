from necrobot.botbase.botchannel import BotChannel
from necrobot.match import cmd_match
from necrobot.user import cmd_user


class CondorMainChannel(BotChannel):
    def __init__(self):
        BotChannel.__init__(self)
        self.command_types = [
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
