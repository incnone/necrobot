import asyncio
import discord
import sqlite3

import config
import raceroom
import raceprivate
import raceinfo
import raceprivateinfo
import racetime
import seedgen

class RaceManager(object):

    def __init__(self, client, server, db_connection):
        self._client = client
        self._server = server
        self._db_conn = db_connection
        self._results_channel = None
        self._races = []
        for channel in self._client.get_all_channels():
            if channel.name == config.RACE_RESULTS_CHANNEL_NAME:
                self._results_channel = channel

    ## Gets the user as a member of the server
    def get_as_member(self, user):
        for member in self._server.members:
            if member.id == user.id:
                return member
        return None

    ## Get a list of all admin roles on the server
    def get_admin_roles(self):
        admin_roles = []
        for rolename in config.ADMIN_ROLE_NAMES:
            for role in self._server.roles:
                if role.name == rolename:
                    admin_roles.append(role)
        return admin_roles
        
    ## Return a new (unique) race room name from the race info
    def get_raceroom_name(self, race_info):
        counter = 0
        trial_name = ''
        while True:
            counter += 1
            trial_name = '{0}_{1}'.format(race_info.raceroom_name(), counter)
            name_is_ok = True
            for c in self._server.channels:
                if c.name == trial_name:
                    name_is_ok = False

            if name_is_ok:
                return trial_name

    ## Make a race with the given RaceInfo
    @asyncio.coroutine
    def make_race(self, race_info):
        #Get rid of closed races (Now seems like a good time to garbage collect)
        self._races = [r for r in self._races if not r.is_closed]
        
        #Make the new race
        race_channel = yield from self._client.create_channel(self._server, self.get_raceroom_name(race_info), type='text')
        new_race = raceroom.RaceRoom(self._client, self, race_channel, race_info)
        self._races.append(new_race)
        asyncio.ensure_future(new_race.initialize())
        return race_channel

##    ## Make a private race with the given RaceInfo
##    @asyncio.coroutine
##    def make_private_race(self, race_private_info):
##        #Get rid of closed races (Now seems like a good time to garbage collect)
##        self._races = [r for r in self._races if not r.is_closed]
##        
##        #Make the new race
##        race_channel = yield from self._client.create_channel(self._server, self.get_raceroom_name(race_private_info.race_info), type='text')
##        new_race = raceprivate.RacePrivate(self._client, self, race_channel, race_private_info)
##        self._races.append(new_race)
##        asyncio.ensure_future(new_race.initialize())
##        return race_channel

    ## Parse a command entered somewhere on the server
    @asyncio.coroutine
    def parse_message(self, message):
        for race in self._races:                
            if race.channel.id == message.channel.id:
                asyncio.ensure_future(race.parse_message(message))

    ## Post a race result in the results channel
    @asyncio.coroutine
    def post_result(self, text):
        if self._results_channel:
            asyncio.ensure_future(self._client.send_message(self._results_channel, text))

