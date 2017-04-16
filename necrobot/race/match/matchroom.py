# Room for scheduling and running a "match", a series of games between a common pool of racers.

from necrobot.botbase import cmd_admin
from necrobot.botbase.botchannel import BotChannel
from necrobot.race.match import cmd_match


def make_match_channel(match):
    pass


class MatchRoom(BotChannel):
    def __init__(self, race_manager, match_discord_channel, race_info):
        BotChannel.__init__(self, race_manager.necrobot)
        self._channel = match_discord_channel   # The necrobot in which this match is taking place
        self._race_info = race_info             # The type of races to be run in this room

        self.command_types = [
            cmd_admin.Help(self),
            cmd_match.Confirm(self),
            cmd_match.Postpone(self),
            cmd_match.Suggest(self),
            cmd_match.Unconfirm(self),
            cmd_match.ForceBegin(self),
            cmd_match.ForceConfirm(self),
            cmd_match.ForceReschedule(self),
            cmd_match.ForceUnschedule(self),
        ]
