#TODO intelligent handling of rate limiting
#TODO mod options for races (assist in cleanup)

## Derived class; makes a private race room

import asyncio
import command
import config
import datetime
import discord
import permissioninfo
import raceroom
import racetime
import random
import sqlite3
import textwrap
import time

from matchinfo import MatchInfo
from permissioninfo import PermissionInfo
from raceinfo import RaceInfo
from racer import Racer

class Ready(raceroom.Ready):
    def __init__(self, race_room):
        raceroom.Ready.__init__(self, race_room)

    @asyncio.coroutine
    def _do_execute(self, command):
        if not self._room.race.is_before_race:
            return

        if self._room.is_race_admin(command.author):
            self._room.admin_ready = True
            yield from self._room.write('Race admins are ready!')
            yield from self._race.begin_if_ready() 
            yield from raceroom.Ready._do_execute(self, command)

class Unready(raceroom.Unready):
    def __init__(self, race_room):
        raceroom.Unready.__init__(self, race_room)

    @asyncio.coroutine
    def _do_execute(self, command):
        if not self._room.race.is_before_race:
            return

        if self._room.is_race_admin(command.author):
            self._room.admin_ready = False
            yield from self._room.write('Race admins are not ready!')
            yield from raceroom.Unready._do_execute(self, command)

class Add(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'add')
        self.help_text = 'Give a user permission to see the room.'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            for username in command.args:
                for member in self._room.find_members(username):
                    yield from self._room.allow(member)
            return True        

class Admins(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'admins')
        self.help_text = 'List all admins for this race.'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        admin_names = ''
        for member in self._room.permission_info.admins:
            admin_names += member.name + ', '
        for role in self._room.permission_info.admin_roles:
            admin_names += role.name + ' (role), '

        if admin_names:
            yield from self._room.write('The admins for this race are: {}'.format(admin_names[:-2]))
        else:
            yield from self._room.write('No admins for this race.')

class Remove(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'remove')
        self.help_text = 'Remove a user\'s permission to see the room.'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            for username in command.args:
                for member in self._room.find_members(username):
                    if not self._room.is_race_admin(member):
                        yield from self._room.deny(member)
            return True        

class ChangeRules(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'changerules')
        self.help_text = 'Change the rules for the race. Takes the same parameters as `.make`.'
        self.suppress_help = True
        self._room = race_room        

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            new_race_info = raceinfo.parse_args_modify(command.args, self._room.race.race_info.copy())
            if new_race_info:
                self._room.race.race_info = new_race_info
                yield from self._room.write('Changed rules for the next race.')
                yield from self._room.race.update_leaderboard()

class MakeAdmin(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'makeadmin')
        self.help_text = 'Make specified users into admins for the race (cannot be undone).'
        self.suppress_help = True
        self._room = race_room        

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            for username in command.args:
                for member in self._room.find_members(username):
                    yield from self._room.allow(member)
                    if not member in self._room.permission_info.admins:
                        self._room.permission_info.admins.append(member)

class Reseed(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'reseed')
        self.help_text = 'Randomly generate a new seed for this race.'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            if self._room.race.race_info.seeded and not self._room.race.race_info.seed_fixed:
                self._room.race.race_info.seed = seedgen.get_new_seed()
                yield from self._room.write('Changed seed to {}.'.format(self._race.race_info.seed))
                yield from self._room.race.update_leaderboard()
            else:
                yield from self._room.write('Cannot reseed this race; it is not a randomly seeded race. Use `.changerules -s` to change this.')

class ForceReset(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'forcereset')
        self.help_text = 'Cancel and reset the current race.'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            yield from self._race.reset()

class Pause(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'pause')
        self.help_text = 'Pause the race timer.'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            success = yield from self._race.pause()
            if success:
                yield from self.write('Race paused by {}!'.format(message.author.mention))

# TODO: countdown the unpause
class Unpause(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'unpause')
        self.help_text = 'Unpause the race timer.'
        self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            success = yield from self._race.unpause()
            if success:
                yield from self.write('Race unpaused! GO!')

class RacePrivateRoom(raceroom.RaceRoom):

    def __init__(self, race_module, race_channel, race_private_info):
        raceroom.RaceRoom.__init__(self, race_module, race_channel, race_private_info.race_info)
        self._match_info = race_private_info.match_info
        self.permission_info = permissioninfo.get_permission_info(race_module.server, race_private_info)
        self.admin_ready = False

        self.command_types = [raceroom.Enter(self),
                              raceroom.Unenter(self),
                              Ready(self),
                              Unready(self),
                              raceroom.Done(self),
                              raceroom.Undone(self),
                              raceroom.Forfeit(self),
                              raceroom.Unforfeit(self),
                              raceroom.Comment(self),
                              raceroom.Igt(self),
                              raceroom.Death(self),
                              raceroom.Rematch(self),
                              raceroom.DelayRecord(self),
                              raceroom.Notify(self),
                              raceroom.Time(self),
                              raceroom.ForceCancel(self),
                              raceroom.ForceClose(self),
                              raceroom.ForceForfeit(self),
                              raceroom.ForceForfeitAll(self),
                              raceroom.Kick(self),
                              Add(self),
                              Admins(self),
                              Remove(self),
                              ChangeRules(self),
                              MakeAdmin(self),
                              Reseed(self),
                              ForceReset(self),
                              Pause(self),
                              Unpause(self)] 

    # Sets up the leaderboard for the race
    # Overrides
    @asyncio.coroutine
    def initialize(self):
        yield from self._set_permissions()
        yield from raceroom.RaceRoom.initialize(self)

    # Makes a rematch of this race in this room, if one has not already been made
    # Overrides
    @asyncio.coroutine
    def make_rematch(self):
        if not self._rematch_made:
            new_race_info = self._race.race_info.copy()
            self._race = Race(self, new_race_info)
            asyncio.ensure_future(self._race.initialize())
            self._rematch_made = True
            yield from self.write('Rematch created!')

    # Begins the race if ready. (Writes a message if all racers are ready but an admin is not.)
    # Overrides
    @asyncio.coroutine
    def begin_if_ready(self):
        success = yield from raceroom.RaceRoom.begin_if_ready(self)
        if success:
            self._rematch_made = False
        return success

    # Find all members with the given username
    def find_members(self, username):
        return self._rm._necrobot.find_members(username)
    
    # True if the user has admin permissions for this race
    # Overrides
    def is_race_admin(self, member):
        return self.permission_info.is_admin(member) or raceroom.RaceRoom.is_race_admin(self, member)

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
        yield from self.deny(self._rm.server.default_role)

        #allow access for self
        yield from self.allow(self._rm.necrobot.get_as_member(self.client.user))

        #give admin roles permission
        for role in self.permission_info.admin_roles:
            yield from self.allow(role)

        #give admins permission
        for member in self.permission_info.admins:
            yield from self.allow(member)

        #give racers permission
        for member in self.permission_info.racers:
            yield from self.allow(member)

##    # Parse chat input.
##    # Overrides
##    @asyncio.coroutine
##    def _derived_parse_message(self, message):
##        args = message.content.split()
##        command = args.pop(0).replace(config.BOT_COMMAND_PREFIX, '', 1)
##
##        #.admins : List race admins
##        if command == 'admins':
##            admin_names = ''
##            for member in self.permission_info.admins:
##                admin_names += member.name + ', '
##            for role in self.permission_info.admin_roles:
##                admin_names += role.name + ' (role), '
##
##            if admin_names:
##                yield from self.write('The admins for this race are: {}'.format(admin_names[:-2]))
##
##        # Admin-only commands
##        if self._is_race_admin(message.author):
##            #.remove : Disallow users from seeing the channel (doesn't work on admins)
##            if command == 'remove':
##                for username in args:
##                    for member in self._manager.find_members_with_name(username):
##                        if not self._is_race_admin(member):
##                            yield from self.deny(member)
##                return True
##
##            # Before the race
##            if self._race.is_before_race:
##                
##                #.add : Allow users to see the channel
##                if command == 'add':
##                    for username in args:
##                        for member in self._manager.find_members_with_name(username):
##                            yield from self.allow(member)
##                    return True
##                
##                #.changerules : Change the rules for the race
##                elif command == 'changerules':
##                    new_race_info = raceinfo.parse_args_modify(args, self._race.race_info.copy())
##                    if new_race_info:
##                        self._race.race_info = new_race_info
##                        yield from self.write('Changed rules for the next race.')
##                        yield from self._race.update_leaderboard()
##                    return True
##                
##                #.makeadmin : Make a user admin for the race (cannot be undone)
##                elif command == 'makeadmin':
##                    for username in args:
##                        for member in self._manager.find_members_with_name(username):
##                            yield from self.allow(member)
##                            if not member in self.permission_info.admins:
##                                self.permission_info.admins.append(member)
##                    return True
##                
##                #.ready : Declare admins ready for race (must be called once by any admin before race can begin, unless no admins)
##                elif command == 'ready':
##                    self._admin_ready = True
##                    if message.author.id in self._race.racers:
##                        return False
##                    else:
##                        yield from self.write('Race admins are ready!')
##                        if self._all_racers_ready():
##                            yield from self._race.begin_race_countdown() 
##                        return True
##                
##                #.reseed : Get a new random seed for the race (only works on seeded races)
##                elif command == 'reseed':
##                    if self._race.race_info.seeded and not self._race.race_info.seed_fixed:
##                        self._race.race_info.seed = seedgen.get_new_seed()
##                        yield from self.write('Changed seed to {}.'.format(self._race.race_info.seed))
##                        yield from self._race.update_leaderboard()
##                    else:
##                        yield from self.write('Cannot reseed this race; it is not a randomly seeded race. Use `.changerules -s` to change this.')
##                    return True
##                
##            # During/After the race:
##            else:
##                
##                #.forcereset : Cancel the race, and return all racers to the entered but not ready state
##                if command == 'forcereset':
##                    yield from self._race.reset()
##                    return True
##                
##                # During the race
##                if not self._race.complete:
##                    #.pause : Pause Necrobot's race timer
##                    if command == 'pause':
##                        success = yield from self._race.pause()
##                        if success:
##                            yield from self.write('Race paused by {}!'.format(message.author.mention))
##                        return True
##
##                    #.unpause : Unpause Necrobot's race timer
##                    elif command == 'unpause':
##                        success = yield from self._race.unpause()
##                        if success:
##                            yield from self.write('Race unpaused! GO!')
##                        return True
##                    
##                # After the race
##                else:
##                    
##                    #.rematch : Overrides. Create a new match in this same room.
##                    if command == 'rematch':
##                        new_race_info = self._race.race_info.copy()
##                        self._race = Race(self, new_race_info)
##                        asyncio.ensure_future(self._race.initialize())
##                        return True
##
##
##        return False
