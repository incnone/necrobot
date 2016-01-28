import asyncio
import discord
import sqlite3

import config
import raceroom
import raceprivateroom
import raceinfo
import raceprivateinfo
import racetime
import seedgen
import userprefs

class RaceManager(object):

    def __init__(self, client, server, db_connection, pref_manager=None):
        self._client = client
        self._server = server
        self._db_conn = db_connection
        self._pref_manager = pref_manager
        self._results_channel = None
        self._races = []
        for channel in self._server.channels:
            if channel.name == config.RACE_RESULTS_CHANNEL_NAME:
                self._results_channel = channel

    ## Move to necrobot
    ## Returns a list of all members with a given username (capitalization ignored)
    def find_members_with_name(self, username):
        to_return = []
        for member in self._server.members:
            if member.name == username:
                to_return.append(member)
        return to_return

    ## Already in necrobot :P
    ## Gets the user as a member of the server
    def get_as_member(self, user):
        for member in self._server.members:
            if member.id == user.id:
                return member
        return None

    ## Move to necrobot
    ## Get a list of all admin roles on the server
    def get_admin_roles(self):
        admin_roles = []
        for rolename in config.ADMIN_ROLE_NAMES:
            for role in self._server.roles:
                if role.name == rolename:
                    admin_roles.append(role)
        return admin_roles

    ## TODO use more unique names so hope to avoid Spot's cacheing on tablet problem
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

    ## Move into .make command for this module
    ## Make a race with the given RaceInfo
    @asyncio.coroutine
    def make_race(self, race_info, creator_id=None, mention=[]):
        #Get rid of closed races (Now seems like a good time to garbage collect)
        self._races = [r for r in self._races if not r.is_closed]
        
        #Make the new race
        race_channel = yield from self._client.create_channel(self._server, self.get_raceroom_name(race_info), type='text')
        new_race = raceroom.RaceRoom(self._client, self, race_channel, race_info)
        new_race.creator_id = creator_id
        self._races.append(new_race)
        asyncio.ensure_future(new_race.initialize(mention))

        # send PM alerts
        if race_channel:
            all_alert_pref = userprefs.UserPrefs()
            all_alert_pref.race_alert = userprefs.RaceAlerts['all']
            alert_string = 'A new race has been started:\nFormat: {1}\nChannel: {0}'.format(race_channel.mention, race_info.format_str())
            for user in self._pref_manager.get_all_matching(all_alert_pref):
                asyncio.ensure_future(self._client.send_message(user, alert_string))
        
        return race_channel

    ## Move into .makeprivate command for this module
    ## Make a private race with the given RaceInfo
    @asyncio.coroutine
    def make_private_race(self, race_private_info, creator_id=None):
        #Get rid of closed races (Now seems like a good time to garbage collect)
        self._races = [r for r in self._races if not r.is_closed]
        
        #Make the new race
        race_channel = yield from self._client.create_channel(self._server, self.get_raceroom_name(race_private_info.race_info), type='text')
        new_race = raceprivateroom.RacePrivateRoom(self._client, self, race_channel, race_private_info)
        new_race.creator_id = creator_id
        self._races.append(new_race)
        asyncio.ensure_future(new_race.initialize())
        return race_channel

    ## Delegate to list of RaceRoom and RacePrivateRoom modules
    ## Parse a command entered somewhere on the server
    @asyncio.coroutine
    def parse_message(self, message):
        for race in self._races:                
            if race.channel.id == message.channel.id:
                asyncio.ensure_future(race.parse_message(message))

    ## Move this functionality into RaceRoom / RacePrivateRoom modules (no reason to have this method here; they have access to client) 
    ## Post a race result in the results channel
    @asyncio.coroutine
    def post_result(self, text):
        if self._results_channel:
            asyncio.ensure_future(self._client.send_message(self._results_channel, text))

    ## Move into RaceRoom / RacePrivateRoom modules
    ## Write something to the main channel
    ## TODO: currently this is called by raceroom, when doing the .rematch command, to announce a rematch
    ## in the bot's main channel. I think its existence suggests some code refactoring should be done around here;
    ## in particular, perhaps this class should be more responsible for messages in the main channel regarding races
    ## at all, and Necrobot should not. One could think of Necrobot as a general structure that takes 'modules', of
    ## which I've coded a race module and a daily module. This seems like a good refactoring.
    @asyncio.coroutine
    def write_in_main(self, text):
        main_channel = None
        for channel in self._server.channels:
            if channel.name == config.MAIN_CHANNEL_NAME:
                main_channel = channel
        if main_channel:
            asyncio.ensure_future(self._client.send_message(main_channel, text))
