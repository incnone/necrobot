# Derived class; makes a private race room

import discord

from .raceroom import RaceRoom
from ..command import privaterace
from ..race import permissioninfo


class PrivateRaceRoom(RaceRoom):
    def __init__(self, race_manager, race_discord_channel, race_private_info, admin_as_member):
        RaceRoom.__init__(self, race_manager, race_discord_channel, race_private_info.race_info)
        self.permission_info = permissioninfo.get_permission_info(self.necrobot.server, race_private_info)
        if admin_as_member not in self.permission_info.admins:
            self.permission_info.admins.append(admin_as_member)

        self.command_types.append(privaterace.Add(self))
        self.command_types.append(privaterace.Remove(self))
        self.command_types.append(privaterace.MakeAdmin(self))
        self.command_types.append(privaterace.ShowAdmins(self))

    # A string to add to the race details ("Private")
    @property
    def format_rider(self):
        return '(private)'

    # Sets up the leaderboard for the race
    async def initialize(self):
        # Set permissions -----------------------------------------
        read_permit = discord.Permissions.none()
        read_permit.read_messages = True

        # deny access to @everyone
        await self.deny(self.necrobot.server.default_role)

        # allow access for self
        await self.allow(self.necrobot.get_as_member(self.client.user))

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

    # Allow the member to see the channel
    async def allow(self, member_or_role):
        read_permit = discord.PermissionOverwrite()
        read_permit.read_messages = True
        await self.client.edit_channel_permissions(self.channel, member_or_role, read_permit)

    # Restrict the member from seeing the channel
    async def deny(self, member_or_role):
        read_deny = discord.PermissionOverwrite()
        read_deny.read_messages = False
        await self.client.edit_channel_permissions(self.channel, member_or_role, read_deny)

    # True if the user has admin permissions for this race
    def _virtual_is_admin(self, member):
        return self.permission_info.is_admin(member)