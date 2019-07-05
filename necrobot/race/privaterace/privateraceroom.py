# Derived class; makes a private race room

import discord

from necrobot.util import server
from necrobot.botbase.necrobot import Necrobot
from necrobot.race.privaterace import permissioninfo, cmd_privaterace
from necrobot.race.publicrace.raceroom import RaceRoom
from necrobot.race.raceutil import get_raceroom_name
from necrobot.util import writechannel
from necrobot.config import Config


# Make a private race with the given RacePrivateInfo; give the given discord_member admin status
async def make_private_room(race_private_info, discord_member):
    # Define permissions
    deny_read = discord.PermissionOverwrite(read_messages=False)
    permit_read = discord.PermissionOverwrite(read_messages=True)

    # Make a channel for the room
    # noinspection PyUnresolvedReferences
    overwrites_dict = {
        server.guild.default_role: deny_read,
        server.guild.me: permit_read,
        discord_member: permit_read
    }
    race_channel = await server.guild.create_text_channel(
        name=get_raceroom_name(race_private_info.race_info),
        overwrites=overwrites_dict
    )

    if race_channel is None:
        return None

    # Put the race channel in the races category
    race_channel_category = server.find_category(channel_name=Config.RACE_CHANNEL_CATEGORY_NAME)
    if race_channel_category is not None:
        await server.set_channel_category(channel=race_channel, category=race_channel_category)

    new_room = PrivateRaceRoom(
        race_discord_channel=race_channel,
        race_private_info=race_private_info,
        admin_as_member=discord_member)
    await new_room.initialize()
    Necrobot().register_bot_channel(race_channel, new_room)

    return race_channel


class PrivateRaceRoom(RaceRoom):
    def __init__(self, race_discord_channel, race_private_info, admin_as_member):
        RaceRoom.__init__(self, race_discord_channel, race_private_info.race_info)
        self._room_creator = admin_as_member

        self.permission_info = permissioninfo.get_permission_info(server.guild, race_private_info)
        if admin_as_member not in self.permission_info.admins:
            self.permission_info.admins.append(admin_as_member)

        self.channel_commands.extend([
            cmd_privaterace.Add(self),
            cmd_privaterace.Remove(self),
            cmd_privaterace.MakeAdmin(self),
            cmd_privaterace.ShowAdmins(self),
            cmd_privaterace.NoPost(self),
            cmd_privaterace.Post(self)
        ])

    # A string to add to the race details ("Private")
    @property
    def format_rider(self):
        return '(private)'

    # Sets up the leaderboard for the race
    async def initialize(self):
        # Set permissions -----------------------------------------
        # give admin roles permission
        for role in self.permission_info.admin_roles:
            await self.allow(role)

        # give admins permission
        for member in self.permission_info.admins:
            await self.allow(member)

        # give racers permission
        for member in self.permission_info.racers:
            await self.allow(member)

        # Initialize base -----------------------------------------
        await RaceRoom.initialize(self)

        # Automatically enter creator into race
        await self.current_race.enter_member(self._room_creator)

    # Allow the member to see the necrobot
    async def allow(self, member_or_role):
        await self.channel.set_permissions(target=member_or_role, read_messages=True)

    # Restrict the member from seeing the necrobot
    async def deny(self, member_or_role):
        await self.channel.set_permissions(target=member_or_role, read_messages=False)

    # True if the user has admin permissions for this race
    def _virtual_is_admin(self, member):
        return self.permission_info.is_admin(member)

    # Close the necrobot.
    async def close(self):
        # If this is a CoNDOR race, log the room text before closing
        if self.race_info.condor_race:
            outfile_name = ''
            for racer in self.current_race.racers:
                outfile_name += '{0}-'.format(racer.member.display_name)
            outfile_name += str(self.channel.id)
            await writechannel.write_channel(self.channel, outfile_name)
        await RaceRoom.close(self)
