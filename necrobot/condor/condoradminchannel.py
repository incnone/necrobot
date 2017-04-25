from necrobot.condor import cmd_condor
from necrobot.gsheet import cmd_sheet
from necrobot.stdconfig import cmd_seedgen
from necrobot.user import cmd_user
from necrobot.botbase.botchannel import BotChannel


class CondorAdminChannel(BotChannel):
    """
    The BotChannel object for a CoNDOR Event #adminchat channel. Various admin functionality, including
    automatching and making matches from a GSheet.
    """
    def __init__(self):
        BotChannel.__init__(self)
        self.command_types = [
            # cmd_condor.Automatch(self),
            # cmd_condor.CloseFinished(self),
            # cmd_condor.DropRacer(self),

            cmd_condor.CloseAllMatches(self),
            cmd_condor.GetCurrentEvent(self),
            cmd_condor.GetMatchRules(self),
            cmd_condor.MakeMatch(self),
            cmd_condor.RegisterCondorEvent(self),
            cmd_condor.SetCondorEvent(self),
            cmd_condor.SetEventName(self),
            cmd_condor.SetMatchRules(self),

            cmd_sheet.GetGSheet(self),
            cmd_sheet.MakeFromSheet(self),
            cmd_sheet.SetGSheet(self),

            cmd_seedgen.RandomSeed(self),

            cmd_user.RTMP(self),
            cmd_user.UserInfo(self),
        ]
