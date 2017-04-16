# Room for scheduling and running a "match", a series of games between a common pool of racers.

import discord
from necrobot.botbase import cmd_admin
from necrobot.botbase.botchannel import BotChannel
from necrobot.race.match import cmd_match
from necrobot.util import console


# Return a new (unique) race room name from the race info
def get_matchroom_name(server, match):
    name_prefix = match.matchroom_name
    cut_length = len(name_prefix) + 1
    largest_postfix = 2

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


async def make_match_room(necrobot, match):
    # Define permissions
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
    new_room = MatchRoom(necrobot, match_channel, match)
    await new_room.initialize()
    necrobot.register_bot_channel(match_channel, new_room)

    return new_room


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

    async def initialize(self):
        pass
