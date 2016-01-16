#TODO intelligent handling of rate limiting
#TODO mod options for races (assist in cleanup)

## Derived class; makes a private race

import asyncio
import datetime
import discord
import racetime
import random
import sqlite3
import textwrap
import time

import config
from permissioninfo import PermissionInfo
from raceinfo import RaceInfo
from racer import Racer
from race import Race

class RacePrivate(Race):

    def __init__(self, discord_client, race_manager, race_channel, race_info, permission_info):
        Race.__init__(self, discord_client, race_manager, race_channel, race_info)
        self._race_permissions = permission_info
        #self._match_info = match_info #TODO: support for best-of-x or repeat-y-times formats
    
    # True if the user has admin permissions for this race
    # Overrides
    def _is_race_admin(self, member):
        for role in member.roles:
            if role in self._manager.get_admin_roles():
                return True
        return self._race_permissions.is_admin(member)

    # Sets up the leaderboard for the race
    # Overrides
    @asyncio.coroutine
    def initialize(self):
        Race.initialize(self)
        yield from self._set_permissions()

    # Make room private to all but admins and racers in permission_info
    @asyncio.coroutine
    def _set_permissions():
        read_permit = discord.Permissions.none()
        read_permit.read_messages = True
            
        yield from self._client.edit_channel_permissions(room_channel, self._server.default_role, deny=read_permit)

        for role in self._race_permissions.admin_roles:
            yield from self._client.edit_channel_permissions(room_channel, admin_role, allow=read_permit)

        for member in self._race_permissions.admins:
            yield from self._client.edit_channel_permissions(room_channel, admin_role, allow=read_permit)

        for member in self._race_permissions.racers:
            yield from self._client.edit_channel_permissions(room_channel, member, allow=read_permit)

    # Parse chat input.
    # Overrides
    @asyncio.coroutine
    def _derived_parse_message(self, message):
        #Override 'enter' & 'join' (?)

        #.remove
        # Before the race
        #.add
        #.admin
        #.changerules
        #.ready
        #.reseed
        # During/After the race:
        #.forcereset
        # During the race
        #.pause
        #.unpause
        # After the race
        #.rematch    
        return False
