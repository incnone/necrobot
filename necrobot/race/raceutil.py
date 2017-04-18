import discord

from necrobot.botbase.necrobot import Necrobot
from necrobot.database import necrodb
from necrobot.race.publicrace.raceroom import RaceRoom
from necrobot.user.userprefs import UserPrefs


# Make a room with the given RaceInfo
async def make_room(race_info):
    necrobot = Necrobot()

    # Make a channel for the room
    race_channel = await necrobot.client.create_channel(
        necrobot.server,
        get_raceroom_name(necrobot.server, race_info),
        type=discord.ChannelType.text)

    if race_channel is not None:
        # Make the actual RaceRoom and initialize it
        new_room = RaceRoom(race_discord_channel=race_channel, race_info=race_info)
        await new_room.initialize()

        necrobot.register_bot_channel(race_channel, new_room)

        # Send PM alerts
        alert_pref = UserPrefs()
        alert_pref.race_alert = True

        alert_string = 'A new race has been started:\nFormat: {1}\nChannel: {0}'.format(
            race_channel.mention, race_info.format_str)
        for member_id in necrodb.get_all_ids_matching_prefs(alert_pref):
            member = necrobot.find_member(discord_id=member_id)
            if member is not None:
                await necrobot.client.send_message(member, alert_string)

    return race_channel


# Return a new (unique) race room name from the race info
def get_raceroom_name(server, race_info):
    name_prefix = race_info.raceroom_name
    cut_length = len(name_prefix) + 1
    largest_postfix = 0
    for channel in server.channels:
        if channel.name.startswith(name_prefix):
            try:
                val = int(channel.name[cut_length:])
                largest_postfix = max(largest_postfix, val)
            except ValueError:
                pass
    return '{0}-{1}'.format(name_prefix, largest_postfix + 1)
