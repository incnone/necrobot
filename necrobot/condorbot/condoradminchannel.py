from necrobot.botbase import cmd_seedgen
from necrobot.botbase.botchannel import BotChannel
from necrobot.gsheet import cmd_sheet
from necrobot.league import cmd_league
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
            cmd_league.CloseAllMatches(self),
            cmd_league.CloseFinished(self),
            cmd_league.Deadline(self),
            cmd_league.DropRacer(self),
            cmd_league.ForceMakeMatch(self),
            cmd_league.GetCurrentEvent(self),
            cmd_league.GetMatchRules(self),
            cmd_league.MakeMatchesFromFile(self),
            cmd_league.RegisterCondorEvent(self),
            cmd_league.ScrubDatabase(self),
            cmd_league.SetCondorEvent(self),
            cmd_league.SetDeadline(self),
            cmd_league.SetEventName(self),
            cmd_league.SetMatchRules(self),

            cmd_sheet.GetGSheet(self),
            cmd_sheet.OverwriteGSheet(self),
            cmd_sheet.SetGSheet(self),

            cmd_seedgen.RandomSeed(self),

            cmd_user.ForceRTMP(self),
            cmd_user.RTMP(self),
            cmd_user.UserInfo(self),

            cmd_test.TestCreateCategory(self),
            cmd_test.TestOverwriteGSheet(self),
        ]
