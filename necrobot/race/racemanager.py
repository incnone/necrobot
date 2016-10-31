# Manages all the racerooms on the necrobot's server

import discord
from ..channel.raceroom import RaceRoom
from ..channel.privateraceroom import PrivateRaceRoom
from ..util.config import Config


class RaceManager(object):
    def __init__(self, necrobot):
        self.necrobot = necrobot
        self._results_channel = necrobot.find_channel(Config.RACE_RESULTS_CHANNEL_NAME)

    @property
    def necrodb(self):
        return self.necrobot.necrodb

    @property
    def results_channel(self):
        return self._results_channel

    # Return a new (unique) race room name from the race info
    def get_raceroom_name(self, race_info):
        name_prefix = race_info.raceroom_name
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

    # Make a room with the given RaceInfo
    async def make_room(self, race_info):
        # Make a channel for the room
        race_channel = await self.necrobot.client.create_channel(
            self.necrobot.server,
            self.get_raceroom_name(race_info),
            type=discord.ChannelType.text)

        if race_channel is not None:
            # Make the actual RaceRoom and initialize it
            new_room = RaceRoom(self, race_channel, race_info)
            await new_room.initialize()

            self.necrobot.register_bot_channel(race_channel, new_room)

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

    async def close_room(self, race_room):
        race_channel = race_room.channel
        self.necrobot.unregister_bot_channel(race_channel)
        await self.necrobot.client.delete_channel(race_channel)

    # Make a private race with the given RacePrivateInfo; give the given discord_member admin status
    async def make_private_room(self, race_private_info, discord_member):
        # Make a channel for the room
        race_channel = await self.necrobot.client.create_channel(
            self.necrobot.server,
            self.get_raceroom_name(race_private_info.race_info),
            type='text')

        if race_channel is not None:
            new_room = PrivateRaceRoom(self, race_channel, race_private_info, discord_member)
            await new_room.initialize()
            self.necrobot.register_bot_channel(race_channel, new_room)

        return race_channel
