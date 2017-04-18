# Room for scheduling and running a "match", a series of games between a common pool of racers.

from necrobot.botbase import cmd_admin
from necrobot.botbase.botchannel import BotChannel
from necrobot.race import cmd_race
from necrobot.race.match import cmd_match
from necrobot.race.race import Race


class MatchRoom(BotChannel):
    def __init__(self, match_discord_channel, match):
        BotChannel.__init__(self)
        self._channel = match_discord_channel   # The necrobot in which this match is taking place
        self._match = match                     # The match for this room

        self._prematch_command_types = [
            cmd_admin.Help(self),

            cmd_match.Confirm(self),
            cmd_match.Suggest(self),
            cmd_match.Unconfirm(self),
            cmd_match.ForceBegin(self),
            cmd_match.ForceConfirm(self),
            cmd_match.ForceReschedule(self),
            cmd_match.Postpone(self),
            cmd_match.RebootRoom(self),
            cmd_match.SetMatchType(self),
            cmd_match.Update(self),
        ]

        self._during_match_command_types = [
            cmd_admin.Help(self),

            cmd_match.CancelRace(self),
            cmd_match.ChangeWinner(self),
            cmd_match.ForceNewRace(self),
            cmd_match.ForceRecordRace(self),
            cmd_match.Postpone(self),
            cmd_match.RebootRoom(self),
            cmd_match.SetMatchType(self),
            cmd_match.Update(self),

            cmd_race.Ready(self),
            cmd_race.Unready(self),
            cmd_race.Done(self),
            cmd_race.Undone(self),
            cmd_race.Time(self),
            cmd_race.Pause(self),
            cmd_race.Unpause(self),
            cmd_race.Reseed(self),
            cmd_race.ChangeRules(self),
            cmd_race.ForceForfeit(self),
            cmd_race.ForceForfeitAll(self),
        ]

        self.command_types = self._prematch_command_types

    @property
    def channel(self):
        return self._channel

    @property
    def match(self):
        return self._match

    @property
    def current_race(self) -> Race:
        # TODO
        pass

    @property
    def last_begun_race(self) -> Race:
        # TODO
        pass

    async def initialize(self):
        pass

    async def update(self):
        pass

    async def write(self, text):
        await self.client.send_message(self.channel, text)
