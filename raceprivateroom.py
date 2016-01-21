#TODO intelligent handling of rate limiting
#TODO mod options for races (assist in cleanup)

## Derived class; makes a private race room

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
from raceroom import RaceRoom

class RacePrivateRoom(RaceRoom):

    def __init__(self, discord_client, race_manager, race_channel, race_private_info):
        RaceRoom.__init__(self, discord_client, race_manager, race_channel, race_private_info.race_info)
        self._match_info = race_private_info.match_info
        self._permission_info = permissioninfo.get_permission_info(race_manager._server, race_private_info)
        self._admin_ready = False
    
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
        yield from RaceRoom.initialize(self)

    # A string to add to the race details ("Private")
    # Overrides
    def format_rider(self):
        return '(private)'

    # Allow the member to see the channel
    @asyncio.coroutine
    def allow(self, member):
        read_permit = discord.Permissions.none()
        read_permit.read_messages = True
        yield from self.client.edit_channel_permissions(self.channel, member, allow=read_permit)

    #Restrict the member from seeing the channel
    @asyncio.coroutine
    def deny(self, member):
        read_permit = discord.Permissions.none()
        read_permit.read_messages = True
        yield from self.client.edit_channel_permissions(self.channel, member, deny=read_permit)        

    # Make room private to all but admins and racers in permission_info
    @asyncio.coroutine
    def _set_permissions(self):
        read_permit = discord.Permissions.none()
        read_permit.read_messages = True

        #deny access to @everyone
        yield from self.deny(self._manager._server.default_role)

        #allow access for self
        yield from self.allow(self._manager.get_as_member(self.client.user))

        #give admin roles permission
        for role in self._permission_info.admin_roles:
            yield from self.allow(role)

        #give admins permission
        for member in self._permission_info.admins:
            yield from self.allow(member)

        #give racers permission
        for member in self._permission_info.racers:
            yield from self.allow(member)

    # Parse chat input.
    # Overrides
    @asyncio.coroutine
    def _derived_parse_message(self, message):
        args = message.content.split()
        command = args.pop(0).replace(config.BOT_COMMAND_PREFIX, '', 1)

        #.admins : List race admins
        if command == 'admins':
            admin_names = ''
            for member in self._permission_info.admins:
                admin_names += member.name + ', '
            for role in self._permission_info.admin_roles:
                admin_names += role.name + ' (role), '

            if admin_names:
                yield from self.write('The admins for this race are: {}'.format(admin_names[:-2]))

        # Admin-only commands
        if self._is_race_admin(message.author):
            #.remove : Disallow users from seeing the channel (doesn't work on admins)
            if command == 'remove':
                for username in args:
                    for member in self._manager.find_members_with_name(username):
                        if not self._is_race_admin(member):
                            yield from self.deny(member)
                return True

            # Before the race
            if self._race.is_before_race:
                
                #.add : Allow users to see the channel
                if command == 'add':
                    for username in args:
                        for member in self._manager.find_members_with_name(username):
                            yield from self.allow(member)
                    return True
                
                #.changerules : Change the rules for the race
                elif command == 'changerules':
                    new_race_info = raceinfo.parse_args_modify(args, self._race.race_info.copy())
                    if new_race_info:
                        self._race.race_info = new_race_info
                        yield from self.write('Changed rules for the next race.')
                        yield from self._race.update_leaderboard()
                    return True
                
                #.makeadmin : Make a user admin for the race (cannot be undone)
                elif command == 'makeadmin':
                    for username in args:
                        for member in self._manager.find_members_with_name(username):
                            yield from self.allow(member)
                            if not member in self._permission_info.admins:
                                self._permission_info.admins.append(member)
                    return True
                
                #.ready : Declare admins ready for race (must be called once by any admin before race can begin, unless no admins)
                elif command == 'ready':
                    self._admin_ready = True
                    if message.author.id in self._race.racers:
                        return False
                    else:
                        yield from self.write('Race admins are ready!')
                        if self._all_racers_ready():
                            yield from self._race.begin_race_countdown() 
                        return True
                
                #.reseed : Get a new random seed for the race (only works on seeded races)
                elif command == 'reseed':
                    if self._race.race_info.seeded and not self._race.race_info.seed_fixed:
                        self._race.race_info.seed = seedgen.get_new_seed()
                        yield from self.write('Changed seed to {}.'.format(self._race.race_info.seed))
                        yield from self._race.update_leaderboard()
                    else:
                        yield from self.write('Cannot reseed this race; it is not a randomly seeded race. Use `.changerules -s` to change this.')
                    return True
                
            # During/After the race:
            else:
                
                #.forcereset : Cancel the race, and return all racers to the entered but not ready state
                if command == 'forcereset':
                    yield from self._race.reset()
                    return True
                
                # During the race
                if not self._race.complete:
                    #.pause : Pause Necrobot's race timer
                    if command == 'pause':
                        success = yield from self._race.pause()
                        if success:
                            yield from self.write('Race paused by {}!'.format(message.author.mention))
                        return True

                    #.unpause : Unpause Necrobot's race timer
                    elif command == 'unpause':
                        success = yield from self._race.unpause()
                        if success:
                            yield from self.write('Race unpaused! GO!')
                        return True
                    
                # After the race
                else:
                    
                    #.rematch : Overrides. Create a new match in this same room.
                    if command == 'rematch':
                        new_race_info = self._race.race_info.copy()
                        self._race = Race(self, new_race_info)
                        asyncio.ensure_future(self._race.initialize())
                        return True


        return False

    # Returns whether the admins are ready.
    @asyncio.coroutine
    def _admin_ready(self):
        return (not self._permission_info.admins and not self._permission_info.admin_roles) or self._admin_ready
