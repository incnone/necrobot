# Room for scheduling and running a "match", a series of games between a common pool of racers.

from .botchannel import BotChannel
from ..command import admin, match


class MatchRoom(BotChannel):
    def __init__(self, race_manager, race_discord_channel, race_info):
        BotChannel.__init__(self, race_manager.necrobot)
        self._channel = race_discord_channel    # The channel in which this match is taking place
        self._race_info = race_info             # The type of races to be run in this room

        self.command_types = [
            admin.Help(self),
            match.Confirm(self),
            match.Postpone(self),
            match.Suggest(self),
            match.Unconfirm(self),
            match.ForceBegin(self),
            match.ForceConfirm(self),
            match.ForceReschedule(self),
            match.ForceUnschedule(self),
        ]
