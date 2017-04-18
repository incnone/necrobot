import discord

from necrobot.botbase.necrobot import Necrobot
from necrobot.database import necrodb
from necrobot.race.match.match import Match
from necrobot.race.match.matchroom import MatchRoom
from necrobot.race.raceinfo import RaceInfo
from necrobot.user import userutil
from necrobot.util import console


class MatchCM(object):
    def __init__(self, match_id):
        self.match = get_match_from_id(match_id)

    def __enter__(self):
        return self.match

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.match.commit()


def make_registered_match(*args, **kwargs):
    match = Match(*args, **kwargs)
    match.commit()
    return match


def get_match_from_id(match_id):
    raw_data = necrodb.get_raw_match_data(match_id)
    if raw_data is not None:
        return make_match_from_raw_db_data(raw_data)
    else:
        return None


def make_match_from_raw_db_data(row):
    race_info = necrodb.get_race_info_from_type_id(int(row[1])) if row[1] is not None else RaceInfo()
    cawmentator = userutil.get_user(user_id=int(row[11])) if row[11] is not None else None

    return Match(
        match_id=int(row[0]),
        race_info=race_info,
        racer_1_id=int(row[2]),
        racer_2_id=int(row[3]),
        suggested_time=row[4],
        r1_confirmed=bool(row[5]),
        r2_confirmed=bool(row[6]),
        r1_unconfirmed=bool(row[7]),
        r2_unconfirmed=bool(row[8]),
        is_best_of=bool(row[9]),
        max_races=int(row[10]),
        cawmentator=cawmentator
    )


# Return a new (unique) race room name from the race info
def get_matchroom_name(server: discord.Server, match: Match) -> str:
    name_prefix = match.matchroom_name
    cut_length = len(name_prefix) + 1
    largest_postfix = 1

    found = False
    for channel in server.channels:
        if channel.name.startswith(name_prefix):
            found = True
            try:
                val = int(channel.name[cut_length:])
                largest_postfix = max(largest_postfix, val)
            except ValueError:
                pass

    return name_prefix if not found else '{0}-{1}'.format(name_prefix, largest_postfix + 1)


def recover_stored_match_rooms():
    for row in necrodb.get_channeled_matches_raw_data():
        channel = Necrobot().find_channel_with_id(int(row[12]))
        if channel is not None:
            match = make_match_from_raw_db_data(row=row)
            new_room = MatchRoom(match_discord_channel=channel, match=match)
            Necrobot().register_bot_channel(channel, new_room)


async def make_match_room(match: Match, register=False) -> MatchRoom or None:
    necrobot = Necrobot()

    # Check to see the match is registered
    if not match.is_registered:
        if register:
            match.commit()
        else:
            return None

    # Check to see if we already have the match channel
    channel_id = necrodb.get_match_channel_id(match.match_id)
    match_channel = necrobot.find_channel_with_id(channel_id) if channel_id is not None else None

    # If we couldn't find the channel or it didn't exist, make a new one
    if match_channel is None:
        # Create permissions
        deny_read = discord.PermissionOverwrite(read_messages=False)
        permit_read = discord.PermissionOverwrite(read_messages=True)
        racer_permissions = []
        for racer in match.racers:
            racer_permissions.append(discord.ChannelPermissions(target=racer.member, overwrite=permit_read))

        # Make a channel for the room
        match_channel = await necrobot.client.create_channel(
            necrobot.server,
            get_matchroom_name(necrobot.server, match),
            discord.ChannelPermissions(target=necrobot.server.default_role, overwrite=deny_read),
            discord.ChannelPermissions(target=necrobot.server.me, overwrite=permit_read),
            *racer_permissions,
            type=discord.ChannelType.text)

        if match_channel is None:
            console.error('Error: Failed to make a match channel.')
            return None

    # Make the actual RaceRoom and initialize it
    necrodb.register_match_channel(match_id=match.match_id, channel_id=match_channel.id)
    new_room = MatchRoom(match_discord_channel=match_channel, match=match)
    necrobot.register_bot_channel(match_channel, new_room)
    await new_room.initialize()

    return new_room


async def close_match_room(match):
    if not match.is_registered:
        console.error('Error: Trying to close the room for an unregistered match.')
        return

    channel_id = necrodb.get_match_channel_id(match.match_id)
    channel = Necrobot().find_channel_with_id(channel_id)
    if channel is None:
        console.error('Error: Coudn\'t find channel with id {0} in close_match_room '
                      '(match_id={1}).'.format(channel_id, match.match_id))
        return

    await Necrobot().unregister_bot_channel(channel)
    await Necrobot().client.delete_channel(channel)
    necrodb.register_match_channel(match_id=match.match_id, channel_id=None)
