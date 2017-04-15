# Room for scheduling and running a "match", a series of games between a common pool of racers.

from necrobot.botbase.botchannel import BotChannel
from necrobot.necrobot import cmdadmin
from necrobot.race.match import command


class MatchRoom(BotChannel):
    def __init__(self, race_manager, race_discord_channel, race_info):
        BotChannel.__init__(self, race_manager.necrobot)
        self._channel = race_discord_channel    # The necrobot in which this match is taking place
        self._race_info = race_info             # The type of races to be run in this room

        self.command_types = [
            cmdadmin.Help(self),
            command.Confirm(self),
            command.Postpone(self),
            command.Suggest(self),
            command.Unconfirm(self),
            command.ForceBegin(self),
            command.ForceConfirm(self),
            command.ForceReschedule(self),
            command.ForceUnschedule(self),
        ]
