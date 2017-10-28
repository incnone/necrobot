from necrobot.ladder import cmd_ladder
from necrobot.user import cmd_user

from necrobot.botbase.botchannel import BotChannel


class LadderChannel(BotChannel):
    def __init__(self):
        BotChannel.__init__(self)
        self.channel_commands = [
            cmd_ladder.LadderDrop(self),
            cmd_ladder.LadderRegister(self),
            cmd_ladder.LadderUnregister(self),
            cmd_ladder.Ranked(self),
            cmd_ladder.Rating(self),
            cmd_ladder.SetAutomatch(self),
            cmd_ladder.Unranked(self),

            cmd_user.RTMP(self),
            cmd_user.SetInfo(self),
            cmd_user.Timezone(self),
            cmd_user.Twitch(self),
            cmd_user.UserInfo(self),
        ]
