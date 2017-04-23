from necrobot.botbase import cmd_admin
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
            cmd_admin.Help(self),
            cmd_admin.Info(self),

            # cmd_condor.Automatch(self),
            # cmd_condor.CloseFinished(self),
            cmd_condor.CloseAllMatches(self),
            # cmd_condor.DropRacer(self),

            cmd_sheet.GetGSheet(self),
            cmd_sheet.MakeFromSheet(self),
            cmd_sheet.SetGSheet(self),

            cmd_seedgen.RandomSeed(self),

            cmd_user.RTMP(self),
            cmd_user.UserInfo(self),
        ]
