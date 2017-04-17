# Room for scheduling and running a "match", a series of games between a common pool of racers.

import discord
from necrobot.botbase import cmd_admin, necrodb
from necrobot.botbase.botchannel import BotChannel
from necrobot.race.match.match import Match
from necrobot.race.match import cmd_match
from necrobot.util import console


# Return a new (unique) race room name from the race info
def get_matchroom_name(server, match):
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


def recover_stored_match_rooms(necrobot):
    for row in necrodb.get_channeled_matches_raw_data():
        channel = necrobot.find_channel_with_id(int(row[12]))
        if channel is not None:
            match = Match.make_from_raw_db_data(necrobot=necrobot, row=row)
            new_room = MatchRoom(necrobot, channel, match)
            necrobot.register_bot_channel(channel, new_room)


async def make_match_room(necrobot, match):
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
    new_room = MatchRoom(necrobot, match_channel, match)
    necrobot.register_bot_channel(match_channel, new_room)
    await new_room.initialize()

    return new_room


async def close_match_room(necrobot, match):
    if not match.is_registered:
        console.error('Error: Trying to close the room for an unregistered match.')
        return

    channel_id = necrodb.get_match_channel_id(match.match_id)
    channel = necrobot.find_channel_with_id(channel_id)
    if channel is None:
        console.error('Error: Coudn\'t find channel with id {0} in close_match_room '
                      '(match_id={1}).'.format(channel_id, match.match_id))
        return

    await necrobot.unregister_bot_channel(channel)
    await necrobot.client.delete_channel(channel)
    necrodb.register_match_channel(match_id=match.match_id, channel_id=None)


class MatchRoom(BotChannel):
    def __init__(self, necrobot, match_discord_channel, match):
        BotChannel.__init__(self, necrobot)
        self._channel = match_discord_channel   # The necrobot in which this match is taking place
        self._match = match                     # The match for this room

        self.command_types = [
            cmd_admin.Help(self),
            cmd_match.Confirm(self),
            cmd_match.Postpone(self),
            cmd_match.Suggest(self),
            cmd_match.Unconfirm(self),
            cmd_match.ForceBegin(self),
            cmd_match.ForceConfirm(self),
            cmd_match.ForceReschedule(self),
            cmd_match.ForceUnschedule(self),
        ]

    @property
    def channel(self):
        return self._channel

    @property
    def match(self):
        return self._match

    async def initialize(self):
        pass
