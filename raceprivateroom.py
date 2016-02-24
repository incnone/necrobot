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
import seedgen
import sqlite3
import textwrap
import time

from matchinfo import MatchInfo
from permissioninfo import PermissionInfo
from raceinfo import RaceInfo
from racer import Racer
from race import Race

class Add(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'add')
        self.help_text = 'Give a user permission to see the room.'
        #self.suppress_help = True
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
        #self.suppress_help = True
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
        #self.suppress_help = True
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
        #self.suppress_help = True
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
        #self.suppress_help = True
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
        #self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            if self._room.race.race_info.seeded and not self._room.race.race_info.seed_fixed:
                self._room.race.race_info.seed = seedgen.get_new_seed()
                yield from self._room.write('Changed seed to {}.'.format(self._room.race.race_info.seed))
                yield from self._room.race.update_leaderboard()
            else:
                yield from self._room.write('Cannot reseed this race; it is not a randomly seeded race. Use `.changerules -s` to change this.')

class ForceReset(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'forcereset')
        self.help_text = 'Cancel and reset the current race.'
        #self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            yield from self._room.race.reset()

class Pause(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'pause')
        self.help_text = 'Pause the race timer.'
        #self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            success = yield from self._room.race.pause()
            if success:
                yield from self.write('Race paused by {}!'.format(message.author.mention))

# TODO: countdown the unpause
class Unpause(command.CommandType):
    def __init__(self, race_room):
        command.CommandType.__init__(self, 'unpause')
        self.help_text = 'Unpause the race timer.'
        #self.suppress_help = True
        self._room = race_room

    @asyncio.coroutine
    def _do_execute(self, command):
        if self._room.is_race_admin(command.author):
            success = yield from self._room.race.unpause()
            if success:
                yield from self.write('Race unpaused! GO!')

class RacePrivateRoom(raceroom.RaceRoom):

    def __init__(self, race_module, race_channel, race_private_info):
        raceroom.RaceRoom.__init__(self, race_module, race_channel, race_private_info.race_info)
        self._match_info = race_private_info.match_info
        self.permission_info = permissioninfo.get_permission_info(race_module.server, race_private_info)

        self.command_types = [command.DefaultHelp(self),
                              raceroom.Enter(self),
                              raceroom.Unenter(self),
                              raceroom.Ready(self),
                              raceroom.Unready(self),
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

    @property
    def infostr(self):
        return 'Private race'

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
            new_race_info = self.race.race_info.copy()
            self.race = Race(self, new_race_info)
            asyncio.ensure_future(self.race.initialize())
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
        return self._rm.necrobot.find_members(username)
    
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
