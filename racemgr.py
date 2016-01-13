import asyncio
import discord
import sqlite3

import race
import raceinfo
import racetime
import seedgen

RACE_RESULTS_CHANNEL_NAME = 'race_results'

class RaceManager(object):

    def __init__(self, client, server, db_connection):
        self._client = client
        self._server = server
        self._db_conn = db_connection
        self._results_channel = None
        self._races = []
        for channel in self._client.get_all_channels():
            if channel.name == RACE_RESULTS_CHANNEL_NAME:
                self._results_channel = channel
        
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
        race_channel = yield from self._client.create_channel(self._server, self.get_raceroom_name(race_info), type='text')
        new_race = race.Race(self._client, race_channel, self._results_channel, race_info)
        self._races.append(new_race)
        asyncio.ensure_future(new_race.initialize())
        return race_channel

    ## Parse a command entered somewhere on the server
    @asyncio.coroutine
    def parse_message(self, message):
        for race in self._races:
            if race.channel.id == message.channel.id:
                asyncio.ensure_future(race.parse_message(message))

