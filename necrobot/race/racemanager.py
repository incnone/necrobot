import discord

from necrobot.botbase.necrodb import NecroDB
from necrobot.race.privaterace.privateraceroom import PrivateRaceRoom
from necrobot.race.race.raceroom import RaceRoom
from ..user.userprefs import UserPrefs
from ..util.config import Config


class RaceManager(object):
    def __init__(self, necrobot):
        self.necrobot = necrobot
        self._results_channel = necrobot.find_channel(Config.RACE_RESULTS_CHANNEL_NAME)

    def refresh(self):
        pass

    def close(self):
        pass

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
        # Make a necrobot for the room
        race_channel = await self.necrobot.client.create_channel(
            self.necrobot.server,
            self.get_raceroom_name(race_info),
            type=discord.ChannelType.text)

        if race_channel is not None:
            # Make the actual RaceRoom and initialize it
            new_room = RaceRoom(self, race_channel, race_info)
            await new_room.initialize()

            self.necrobot.register_bot_channel(race_channel, new_room)

            # Send PM alerts
            alert_pref = UserPrefs()
            alert_pref.race_alert = True

            alert_string = 'A new race has been started:\nFormat: {1}\nChannel: {0}'.format(
                race_channel.mention, race_info.format_str)
            for member_id in NecroDB().get_all_ids_matching_prefs(alert_pref):
                member = self.necrobot.find_member(discord_id=member_id)
                if member is not None:
                    await self.necrobot.client.send_message(member, alert_string)

        return race_channel

    async def close_room(self, race_room):
        race_channel = race_room.channel
        self.necrobot.unregister_bot_channel(race_channel)
        await self.necrobot.client.delete_channel(race_channel)

    # Make a private race with the given RacePrivateInfo; give the given discord_member admin status
    async def make_private_room(self, race_private_info, discord_member):
        # Make a necrobot for the room
        race_channel = await self.necrobot.client.create_channel(
            self.necrobot.server,
            self.get_raceroom_name(race_private_info.race_info),
            type='text')

        if race_channel is not None:
            new_room = PrivateRaceRoom(self, race_channel, race_private_info, discord_member)
            await new_room.initialize()
            self.necrobot.register_bot_channel(race_channel, new_room)

        return race_channel
