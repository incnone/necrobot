# Manages all the racerooms on the necrobot's server

import discord
from ..race import raceroom, raceprivateroom
from ..util import config


class RaceManager(object):
    def __init__(self, necrobot):
        self.necrobot = necrobot
        self._results_channel = necrobot.find_channel(config.RACE_RESULTS_CHANNEL_NAME)
        self._racerooms = []
        # TODO garbage collect closed race rooms

    @property
    def necrodb(self):
        return self.necrobot.necrodb

    @property
    def results_channel(self):
        return self._results_channel

    # Return a new (unique) race room name from the race info
    def get_raceroom_name(self, race_info):
        name_prefix = race_info.raceroom_name()
        cut_length = len(name_prefix) + 1
        largest_postfix = 0
        for channel in self.necrobot.server.channels:
            if channel.name.startswith(name_prefix):
                try:
                    val = int(channel.name[cut_length:])
                    largest_postfix = max(largest_postfix, val)
                except ValueError:
                    pass
        return '{0}-{1}'.format(name_prefix, largest_postfix + 1)

    # Make a race with the given RaceInfo
    async def make_room(self, race_info):
        # Make a channel for the race
        race_channel = await self.necrobot.client.create_channel(
            self.necrobot.server, self.get_raceroom_name(race_info), type=discord.ChannelType.text)

        if race_channel:
            # Make the actual RaceRoom and initialize it
            new_room = raceroom.RaceRoom(self, race_channel, race_info)
            self._racerooms.append(new_room)
            await new_room.initialize()

            # TODO Send PM alerts
            # # Send PM alerts
            # alert_pref = userprefs.UserPrefs()
            # alert_pref.race_alert = userprefs.RaceAlerts['some']
            #
            # alert_string = 'A new race has been started:\nFormat: {1}\nChannel: {0}'.format(
            #     race_channel.mention, race_info.format_str())
            # for user in self.necrobot.prefs.get_all_matching(alert_pref):
            #     asyncio.ensure_future(self.client.send_message(user, alert_string))

        return race_channel

    # Make a private race with the given RacePrivateInfo
    async def make_private_room(self, race_private_info):
        # Make the new race
        race_channel = await self.necrobot.client.create_channel(
            self.necrobot.server,
            self.get_raceroom_name(race_private_info.race_info),
            type='text')
        new_room = raceprivateroom.RacePrivateRoom(self, race_channel, race_private_info)
        self._racerooms.append(new_room)
        await new_room.initialize()
        return race_channel
