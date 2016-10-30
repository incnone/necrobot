# A room where racing is happening

import asyncio
import datetime
import time

from .botchannel import BotChannel
from ..command import admin
from ..command import race
from ..race.race import Race
from ..util import config


class RaceRoom(BotChannel):
    def __init__(self, race_manager, race_discord_channel, race_info):
        BotChannel.__init__(self, race_manager.necrobot)
        self.channel = race_discord_channel     # The channel in which this race is taking place
        self.is_closed = False                  # True if the associated discord channel has been closed
        self.race_info = race_info              # The type of races to be run in this room
        self.race = None                        # The current race

        self._race_manager = race_manager       # The parent managing all race rooms
        self._mention_on_new_race = []          # A list of users that should be @mentioned when a rematch is created
        self._nopoke = False                    # When True, the .poke command fails

        self.command_types = [admin.Help(self),
                              race.Enter(self),
                              race.Unenter(self),
                              race.Ready(self),
                              race.Unready(self),
                              race.Done(self),
                              race.Undone(self),
                              race.Forfeit(self),
                              race.Unforfeit(self),
                              race.Comment(self),
                              race.Death(self),
                              race.Igt(self),
                              race.Rematch(self),
                              race.DelayRecord(self),
                              race.Notify(self),
                              race.Time(self),
                              race.Missing(self),
                              race.Shame(self),
                              race.Poke(self),
                              race.ForceCancel(self),
                              race.ForceClose(self),
                              race.ForceForfeit(self),
                              race.ForceForfeitAll(self),
                              race.ForceRecord(self),
                              race.Kick(self)]

    @property
    def client(self):
        return self.necrobot.client

    # A string to add to the race details (used for private races; empty in base class)
    @property
    def format_rider(self):
        return ''

    # Notifies the given user on a rematch
    def notify(self, user):
        if user not in self._mention_on_new_race:
            self._mention_on_new_race.append(user)

    # Removes notifications for the given user on rematch
    def dont_notify(self, user):
        self._mention_on_new_race = [u for u in self._mention_on_new_race if u != user]

    # True if the user has admin permissions for this race
    def is_race_admin(self, member):
        admin_roles = self.necrobot.admin_roles
        for role in member.roles:
            if role in admin_roles:
                return True

        return False

    # Set up the leaderboard etc. Should be called after creation; code not put into __init__ b/c coroutine
    async def initialize(self):
        asyncio.ensure_future(self._monitor_for_cleanup())
        await self._make_new_race()

    # Write text to the raceroom. Return a Message for the text written
    async def write(self, text):
        return self.client.send_message(self.channel, text)

    # Updates the leaderboard
    async def update_leaderboard(self):
        await self.client.edit_channel(self.channel, topic=self.race.leaderboard)

    # Close the channel.
    async def close(self):
        await self.client.delete_channel(self.channel)
        self.is_closed = True

    # Makes a rematch of this race if the current race is finished
    async def make_rematch(self):
        if self.race.complete:
            await self._make_new_race()

    # TODO: more intelligent result posting
    # Post the race result to the race channel
    async def post_result(self, text):
        await self.client.send_message(self._race_manager.results_channel, text)

    # Alerts unready users
    async def poke(self):
        if self._nopoke:
            return

        ready_racers = []
        unready_racers = []
        for racer in self.race.racers.values():
            if racer.is_ready:
                ready_racers.append(racer)
            else:
                unready_racers.append(racer)

        num_unready = len(unready_racers)
        quorum = (num_unready == 1) or (3*num_unready <= len(ready_racers))

        if ready_racers and quorum:
            self._nopoke = True
            alert_string = ''
            for racer in unready_racers:
                alert_string += racer.member.mention + ', '
            await self.write('Poking {0}.'.format(alert_string[:-2]))
            asyncio.ensure_future(self.run_nopoke_delay())

    # Implements a delay before pokes can happen again
    async def run_nopoke_delay(self):
        await asyncio.sleep(config.RACE_POKE_DELAY)
        self._nopoke = False

    # Makes a new Race, overwriting the old one
    async def _make_new_race(self):
        # Make the race
        self.race = Race(self)
        await self.race.initialize()
        await self.update_leaderboard()

        # Send @mention message
        mention_text = ''
        for user in self._mention_on_new_race:
            mention_text += user.mention + ' '
        if mention_text:
            await self.client.send_message(self.channel, mention_text)

        # Print seed in chat
        if self.race.race_info.seeded:
            await self.client.send_message(
                self.channel, 'The seed for this race is {0}.'.format(self.race.race_info.seed))

    # Checks to see whether the room should be cleaned.
    async def _monitor_for_cleanup(self):
        # Pre-race cleanup loop
        while not self.is_closed:
            await asyncio.sleep(30)  # Wait between check times

            # Pre-race
            if self.race.before_race:
                if (not self.race.racers) and self.race.no_entrants_time:
                    if time.monotonic() - self.race.no_entrants_time > config.NO_ENTRANTS_CLEANUP_WARNING_SEC:
                        time_remaining = config.NO_ENTRANTS_CLEANUP_SEC - config.NO_ENTRANTS_CLEANUP_WARNING_SEC
                        await self.write(
                            'Warning: Race has had zero entrants for some time and will be closed in {} '
                            'seconds.'.format(time_remaining))
                        await asyncio.sleep(time_remaining)
                        if not self.race.racers:
                            await self.close()
                            return

            # Post-race
            elif self.race.complete:
                msg_list = await self.client.logs_from(self.channel, 1)
                for msg in msg_list:
                    if (datetime.datetime.utcnow() - msg.timestamp).total_seconds() > config.CLEANUP_TIME_SEC:
                        await self.close()
                        return
