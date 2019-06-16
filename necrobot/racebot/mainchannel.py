from necrobot.botbase import cmd_seedgen
from necrobot.botbase import cmd_admin
from necrobot.botbase.botchannel import BotChannel
from necrobot.race import cmd_racemake
from necrobot.race import cmd_racestats
from necrobot.speedrun import cmd_speedrun
# from necrobot.ladder import cmd_ladder
from necrobot.botbase import cmd_color, cmd_role
from necrobot.user import cmd_user


class MainBotChannel(BotChannel):
    def __init__(self):
        BotChannel.__init__(self)
        self.channel_commands = [
            cmd_admin.Die(self),
            # cmd_admin.Reboot(self),

            cmd_color.ColorMe(self),

            # cmd_ladder.ForceRanked(self),
            # cmd_ladder.Ranked(self),
            # cmd_ladder.Rating(self),
            # cmd_ladder.Unranked(self),

            cmd_racemake.Make(self),
            cmd_racemake.MakeCondor(self),
            cmd_racemake.MakePrivate(self),

            cmd_racestats.Fastest(self),
            cmd_racestats.MostRaces(self),
            cmd_racestats.Stats(self),

            cmd_role.AddCRoWRole(self),
            cmd_role.RemoveCRoWRole(self),

            cmd_seedgen.RandomSeed(self),

            # cmd_speedrun.Submit(self),

            cmd_user.DailyAlert(self),
            cmd_user.RaceAlert(self),
            cmd_user.RTMP(self),
            cmd_user.SetInfo(self),
            cmd_user.Timezone(self),
            cmd_user.Twitch(self),
            cmd_user.ViewPrefs(self),
            cmd_user.UserInfo(self),
        ]
