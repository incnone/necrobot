from necrobot.botbase import cmd_seedgen
from necrobot.botbase.botchannel import BotChannel
from necrobot.condorbot import cmd_event
from necrobot.gsheet import cmd_sheet
from necrobot.league import cmd_league
# from necrobot.speedrun import cmd_speedrun
from necrobot.user import cmd_user
from necrobot.test import cmd_test


class CondorAdminChannel(BotChannel):
    """
    The BotChannel object for a CoNDOR Event #adminchat channel. Various admin functionality, including
    automatching and making matches from a GSheet.
    """
    def __init__(self):
        BotChannel.__init__(self)
        self.channel_commands = [
            cmd_event.Deadline(self),
            cmd_event.GetCurrentEvent(self),
            cmd_event.RegisterCondorEvent(self),
            cmd_event.ScrubDatabase(self),
            cmd_event.SetCondorEvent(self),
            cmd_event.SetDeadline(self),
            cmd_event.SetEventName(self),

            cmd_league.CloseAllMatches(self),
            cmd_league.CloseFinished(self),

            cmd_league.DropRacer(self),
            cmd_league.ForceMakeMatch(self),
            cmd_league.GetLeagueInfo(self),
            cmd_league.MakeLeague(self),
            cmd_league.MakeMatchesFromFile(self),
            cmd_league.SetLeagueName(self),
            cmd_league.SetMatchRules(self),

            cmd_sheet.GetGSheet(self),
            cmd_sheet.OverwriteGSheet(self),
            cmd_sheet.SetGSheet(self),

            cmd_seedgen.RandomSeed(self),

            # cmd_speedrun.OverwriteSpeedrunGSheet(self),
            # cmd_speedrun.SetSpeedrunGSheet(self),
            # cmd_speedrun.Verify(self),

            cmd_user.ForceRTMP(self),
            cmd_user.RTMP(self),
            cmd_user.UserInfo(self),

            cmd_test.TestCreateCategory(self),
            cmd_test.TestOverwriteGSheet(self),
        ]
