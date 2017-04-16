# A room where racing is happening

import asyncio
import datetime

from necrobot.botbase import cmd_admin
from necrobot.botbase.botchannel import BotChannel
from necrobot.race.race import cmd_race, raceinfo
from necrobot.race.race.race import Race
from necrobot.util import seedgen
from necrobot.util.config import Config


class RaceRoom(BotChannel):
    def __init__(self, race_manager, race_discord_channel, race_info):
        BotChannel.__init__(self, race_manager.necrobot)
        self._channel = race_discord_channel    # The necrobot in which this race is taking place
        self._race_info = race_info             # The type of races to be run in this room

        self._current_race = None               # The current race
        self._last_race = None                  # The last race to finish

        self._race_manager = race_manager       # The parent managing all race rooms
        self._race_number = 0                   # The number of races we've done
        self._mention_on_new_race = []          # A list of users that should be @mentioned when a rematch is created
        self._mentioned_users = []              # A list of users that were @mentioned when this race was created
        self._nopoke = False                    # When True, the .poke command fails

        self.command_types = [cmd_admin.Help(self),
                              cmd_race.Enter(self),
                              cmd_race.Unenter(self),
                              cmd_race.Ready(self),
                              cmd_race.Unready(self),
                              cmd_race.Done(self),
                              cmd_race.Undone(self),
                              cmd_race.Forfeit(self),
                              cmd_race.Unforfeit(self),
                              cmd_race.Comment(self),
                              cmd_race.Death(self),
                              cmd_race.Igt(self),
                              cmd_race.Rematch(self),
                              cmd_race.DelayRecord(self),
                              cmd_race.Notify(self),
                              cmd_race.Unnotify(self),
                              cmd_race.Time(self),
                              cmd_race.Missing(self),
                              cmd_race.Shame(self),
                              cmd_race.Poke(self),
                              cmd_race.ForceCancel(self),
                              cmd_race.ForceClose(self),
                              cmd_race.ForceForfeit(self),
                              cmd_race.ForceForfeitAll(self),
                              cmd_race.Kick(self),
                              cmd_race.Pause(self),
                              cmd_race.Unpause(self),
                              cmd_race.Reseed(self),
                              cmd_race.ChangeRules(self)]

# Properties ------------------------------
    @property
    def channel(self):
        return self._channel

    @property
    def client(self):
        return self.necrobot.client

    # The currently active race. Is not None.
    @property
    def current_race(self):
        return self._current_race

    # A string to add to the race details (used for private races; empty in base class)
    @property
    def format_rider(self):
        return ''

    # The most recent race to begin, or None if no such
    @property
    def last_begun_race(self):
        if not self._current_race.before_race:
            return self._current_race
        else:
            return self._last_race

    @property
    def mentioned_users(self):
        return self._mentioned_users

    @property
    def race_info(self):
        return self._race_info

# Methods -------------------------------------------------------------
    # Notifies the given user on a rematch
    def notify(self, user):
        if user not in self._mention_on_new_race:
            self._mention_on_new_race.append(user)

    # Removes notifications for the given user on rematch
    def dont_notify(self, user):
        self._mention_on_new_race = [u for u in self._mention_on_new_race if u != user]

    def refresh(self, channel):
        self._channel = channel

# Coroutine methods ---------------------------------------------------
    # Set up the leaderboard etc. Should be called after creation; code not put into __init__ b/c coroutine
    async def initialize(self):
        asyncio.ensure_future(self._monitor_for_cleanup())
        await self._make_new_race()
        await self.write('Enter the race with `.enter`, and type `.ready` when ready. '
                         'Finish the race with `.done` or `.forfeit`. Use `.help` for a command list.')

    # Write text to the raceroom. Return a Message for the text written
    async def write(self, text):
        await self.client.send_message(self._channel, text)

    # Updates the leaderboard
    async def update_leaderboard(self):
        await self.client.edit_channel(self._channel, topic=self._current_race.leaderboard)

    # Post the race result to the race necrobot
    async def post_result(self, text):
        await self.client.send_message(self._race_manager.results_channel, text)

# Commands ------------------------------------------------------------
    async def set_post_result(self, do_post):
        self._race_info.post_results = do_post
        if self.current_race.before_race:
            self.current_race.race_info = raceinfo.RaceInfo.copy(self._race_info)
        if do_post:
            await self.write('Races in this necrobot will have their results posted to the results necrobot.')
        else:
            await self.write('Races in this necrobot will not have their results posted to the results necrobot.')

    # Change the RaceInfo for this room
    async def change_race_info(self, command_args):
        new_race_info = raceinfo.parse_args_modify(command_args, raceinfo.RaceInfo.copy(self._race_info))
        if new_race_info:
            self._race_info = new_race_info
            if self.current_race.before_race:
                self.current_race.race_info = raceinfo.RaceInfo.copy(self._race_info)
            await self.write('Changed rules for the next race.')
            await self.update_leaderboard()

    # Close the necrobot.
    async def close(self):
        await self._race_manager.close_room(self)

    # Makes a rematch of this race if the current race is finished
    async def make_rematch(self):
        if self._current_race.complete:
            await self._make_new_race()

    # Pause the race
    async def pause(self):
        if self._current_race.during_race:
            await self._current_race.pause()
            mention_str = ''
            for racer in self._current_race.racers:
                mention_str += '{}, '.format(racer.member.mention)
            mention_str = mention_str[:-2]

            await self.write('Race paused. (Alerting {0}.)'.format(mention_str))

    # Unpause the race
    async def unpause(self):
        if self._current_race.paused:
            await self._current_race.unpause()

    # Alerts unready users
    async def poke(self):
        if self._nopoke or not self._current_race or not self._current_race.before_race:
            return

        ready_racers = []
        unready_racers = []
        for racer in self._current_race.racers.values():
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
            asyncio.ensure_future(self._run_nopoke_delay())

    # Reseed the race
    async def reseed(self):
        if not self._current_race.race_info.seeded:
            await self.write('This is not a seeded race. Use `.newrules` to change this.')

        elif self._current_race.race_info.seed_fixed:
            await self.write('The seed for this race was fixed by its rules. Use `.newrules` to change this.')
            return

        else:
            self._current_race.race_info.seed = seedgen.get_new_seed()
            await self.write('Changed seed to {0}.'.format(self._current_race.race_info.seed))
            await self.update_leaderboard()

# Private -----------------------------------------------------------------
    # Makes a new Race, overwriting the old one
    async def _make_new_race(self):
        # Make the race
        self._race_number += 1
        self._last_race = self._current_race
        self._current_race = Race(self)
        await self._current_race.initialize()
        await self.update_leaderboard()

        # Send @mention message
        self._mentioned_users = []
        mention_text = ''
        for user in self._mention_on_new_race:
            mention_text += user.mention + ' '
            self._mentioned_users.append(user)

        self._mention_on_new_race = []

        if self.race_info.seeded:
            await self.client.send_message(
                self._channel,
                '{0}\nRace number {1} is open for entry. Seed: {2}.'.format(
                    mention_text, self._race_number, self.current_race.race_info.seed))
        else:
            await self.client.send_message(
                self._channel,
                '{0}\nRace number {1} is open for entry.'.format(mention_text, self._race_number))

    # Checks to see whether the room should be cleaned.
    async def _monitor_for_cleanup(self):
        while True:
            await asyncio.sleep(30)  # Wait between check times

            # No race object
            if self._current_race is None:
                await self.close()
                return

            # Pre-race
            elif self._current_race.before_race:
                if not self._current_race.any_entrants:
                    if self._current_race.passed_no_entrants_cleanup_time:
                        await self.close()
                        return
                    elif self._current_race.passed_no_entrants_warning_time:
                        await self.write('Warning: Race has had zero entrants for some time and will be closed soon.')

            # Post-race
            elif self._current_race.complete:
                async for msg in self.client.logs_from(self._channel, 1):
                    if (datetime.datetime.utcnow() - msg.timestamp).total_seconds() > Config.CLEANUP_TIME_SEC:
                        await self.close()
                        return

    # Implements a delay before pokes can happen again
    async def _run_nopoke_delay(self):
        await asyncio.sleep(Config.RACE_POKE_DELAY)
        self._nopoke = False
