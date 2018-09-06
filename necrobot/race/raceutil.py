import discord

from necrobot.botbase.necrobot import Necrobot
from necrobot.config import Config
from necrobot.race.publicrace.raceroom import RaceRoom
from necrobot.user.userprefs import UserPrefs
from necrobot.util import console
from necrobot.util import server
from necrobot.user import userdb


# Make a room with the given RaceInfo
async def make_room(race_info):
    # Make a channel for the room
    race_channel = await server.client.create_channel(
        server.server,
        get_raceroom_name(race_info),
        type=discord.ChannelType.text)

    if race_channel is None:
        console.warning('Failed to make a race channel.')
        return None

    # Put the race channel in the races category
    race_channel_category = server.find_channel(channel_name=Config.RACE_CHANNEL_CATEGORY_NAME)
    if race_channel_category is not None:
        await server.set_channel_category(channel=race_channel, category=race_channel_category)

    # Make the actual RaceRoom and initialize it
    new_room = RaceRoom(race_discord_channel=race_channel, race_info=race_info)
    await new_room.initialize()

    Necrobot().register_bot_channel(race_channel, new_room)

    # Send PM alerts
    alert_pref = UserPrefs(daily_alert=None, race_alert=True)

    alert_string = 'A new race has been started:\nFormat: {1}\nChannel: {0}'.format(
        race_channel.mention, race_info.format_str)
    for member_id in await userdb.get_all_discord_ids_matching_prefs(alert_pref):
        member = server.find_member(discord_id=member_id)
        if member is not None:
            try:
                await server.client.send_message(member, alert_string)
            except discord.errors.Forbidden:
                continue

    return race_channel


# Return a new (unique) race room name from the race info
def get_raceroom_name(race_info):
    name_prefix = race_info.raceroom_name
    cut_length = len(name_prefix) + 1
    largest_postfix = 0
    for channel in server.server.channels:
        if channel.name.startswith(name_prefix):
            try:
                val = int(channel.name[cut_length:])
                largest_postfix = max(largest_postfix, val)
            except ValueError:
                pass
    return '{0}-{1}'.format(name_prefix, largest_postfix + 1)
