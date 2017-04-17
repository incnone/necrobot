# Room for scheduling and running a "match", a series of games between a common pool of racers.

from necrobot.botbase import cmd_admin
from necrobot.botbase.botchannel import BotChannel
from necrobot.race.match import cmd_match


class MatchRoom(BotChannel):
    def __init__(self, match_discord_channel, match):
        BotChannel.__init__(self)
        self._channel = match_discord_channel   # The necrobot in which this match is taking place
        self._match = match                     # The match for this room

        self.command_types = [
            cmd_admin.Help(self),
            cmd_match.Confirm(self),
            cmd_match.Suggest(self),
            cmd_match.Unconfirm(self),
            cmd_match.ForceBegin(self),
            cmd_match.ForceConfirm(self),
            cmd_match.ForceReschedule(self),
            cmd_match.ForceUnschedule(self),
            cmd_match.Postpone(self),
            cmd_match.RebootRoom(self),
            cmd_match.SetMatchType(self),
            cmd_match.Update(self),
        ]

    @property
    def channel(self):
        return self._channel

    @property
    def match(self):
        return self._match

    async def initialize(self):
        pass

    async def update(self):
        pass
