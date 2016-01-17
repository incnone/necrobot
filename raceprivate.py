#TODO intelligent handling of rate limiting
#TODO mod options for races (assist in cleanup)

## Derived class; makes a private race

import asyncio
import datetime
import discord
import permissioninfo
import racetime
import random
import sqlite3
import textwrap
import time

import config
from matchinfo import MatchInfo
from permissioninfo import PermissionInfo
from raceinfo import RaceInfo
from racer import Racer
from race import Race

class RacePrivate(Race):

    def __init__(self, discord_client, race_manager, race_channel, race_private_info):
        Race.__init__(self, discord_client, race_manager, race_channel, race_private_info.race_info)
        self._match_info = race_private_info.match_info
        self._permission_info = permissioninfo.get_permission_info(race_manager._server, race_private_info)
    
    # True if the user has admin permissions for this race
    # Overrides
    def _is_race_admin(self, member):
        for role in member.roles:
            if role in self._manager.get_admin_roles():
                return True
        return self._permission_info.is_admin(member)

    # Sets up the leaderboard for the race
    # Overrides
    @asyncio.coroutine
    def initialize(self):
        yield from self._set_permissions()
        yield from Race.initialize(self)

    # Make room private to all but admins and racers in permission_info
    @asyncio.coroutine
    def _set_permissions(self):
        read_permit = discord.Permissions.none()
        read_permit.read_messages = True
            
        yield from self._client.edit_channel_permissions(self.channel, self._manager._server.default_role, deny=read_permit)

        #give self permission
        yield from self._client.edit_channel_permissions(self.channel, self._manager.get_as_member(self._client.user), allow=read_permit)

        #give admin roles permission
        for role in self._permission_info.admin_roles:
            yield from self._client.edit_channel_permissions(self.channel, role, allow=read_permit)

        #give admins permission
        for member in self._permission_info.admins:
            yield from self._client.edit_channel_permissions(self.channel, member, allow=read_permit)

        #give racers permission
        for member in self._permission_info.racers:
            yield from self._client.edit_channel_permissions(self.channel, member, allow=read_permit)

    # Parse chat input.
    # Overrides
    @asyncio.coroutine
    def _derived_parse_message(self, message):
        #.remove : Disallow a user from seeing the channel (doesn't work on admins)
        # Before the race
        #.add : Allow a user to see the channel
        #.admin : Make a user admin for the race (cannot be undone)
        #.changerules : Change the rules for the race
        #.ready : Declare self ready for race (used for admins that haven't entered the race) 
        #.reseed : Get a new random seed for the race (only works on seeded races)
        # During/After the race:
        #.forcereset : Cancel the race, and return all racers to the entered but not ready state
        # During the race
        #.pause : Pause Necrobot's race timer
        #.unpause : Unpause Necrobot's race timer
        # After the race
        #.rematch : Overrides. Create a new race in this same room.
        return False
