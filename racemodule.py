import asyncio
import discord
import sqlite3

import command
import config
import raceroom
import raceprivateroom
import raceinfo
import raceprivateinfo
import racetime
import seedgen
import userprefs

class Make(command.CommandType):
    def __init__(self, race_module):
        command.CommandType.__init__(self, 'make')
        self.help_text = "Create a new race room. By default this creates an unseeded Cadence race, " \
                    "but there are optional parameters. First, the short form:\n" \
                    "```" \
                    ".make [char] [u|s]" \
                    "```" \
                    "makes a race with the given character and seeding options; `char` should be a Necrodancer character, and " \
                    "the other field is either the letter `u` or the letter `s`, according to whether the race should be seeded " \
                    "or unseeded. Examples: `.make dorian u` or `.make s dove` are both fine.\n" \
                    "\n" \
                    "More options are available using usual command-line syntax:" \
                    "```" \
                    ".make [-c char] [-u|-s|-seed number] [-custom desc]" \
                    "```" \
                    "makes a race with character char, and seeded/unseeded determined by the `-u` or `-s` flag. If instead number is specified, " \
                    "the race will be seeded and forced to use the seed given. Number must be an integer (text seeds are not currently supported). " \
                    "Finally, desc allows you to give any custom one-word description of the race (e.g., '4-shrine')."
        self._rm = race_module

    @asyncio.coroutine
    def _do_execute(self, command):
        if command.channel == self._rm.main_channel:
            race_info = raceinfo.parse_args(command.args)
            if race_info:
                race_channel = yield from self._rm.make_race(race_info, creator=command.author, suppress_alerts=True)
                if race_channel:
                    alert_string = 'A new race has been started:\nFormat: {1}\nChannel: {0}'.format(race_channel.mention, race_info.format_str())
                    main_channel_string = 'A new race has been started by {0}:\nFormat: {2}\nChannel: {1}'.format(command.author.mention, race_channel.mention, race_info.format_str())

                    # send PM alerts
                    some_alert_pref = userprefs.UserPrefs()
                    some_alert_pref.race_alert = userprefs.RaceAlerts['some']
                    for user in self._rm.prefs.get_all_matching(some_alert_pref):
                        asyncio.ensure_future(self._rm.client.send_message(user, alert_string))

                    # alert in main channel
                    asyncio.ensure_future(self._rm.client.send_message(command.channel, main_channel_string))

class MakePrivate(command.CommandType):
    def __init__(self, race_module):
        command.CommandType.__init__(self, 'makeprivate')
        self.help_text = "Create a new private race room. This takes the same command-line options as `.make`, as well as " \
                    "two more, for specifying room permissions:\n" \
                    "```" \
                    ".makeprivate [-a admin...] [-r racer...]" \
                    "```" \
                    "Here `admin...` is a list of names of 'admins' for the race, which are users that can both see the race channel and " \
                    "use special admin commands for managing the race, and `racer...` is a list of users that can see the race channel. " \
                    "(Both admins and racers can enter the race, or not, as they prefer.)"                 
        self._rm = race_module

    @asyncio.coroutine
    def _do_execute(self, command):
        if command.channel.is_private or command.channel == self._rm.main_channel:
            race_private_info = raceprivateinfo.parse_args(args)
            if not command.author.name in race_private_info.admin_names:
                race_private_info.admin_names.append(command.author.name)
            if race_private_info:
                race_channel = yield from self._rm.make_private_race(race_private_info, creator=command.author)
                if race_channel:
                    output_prestring = 'You have started a private race.' if command.channel.is_private else 'A private race has been started by {}.'.format(command.author.mention)
                    asyncio.ensure_future(self.client.send_message(command.channel,
                        '{0}\nFormat: {2}\nChannel: {1}'.format(output_prestring, race_channel.mention, race_private_info.race_info.format_str())))             

class RaceModule(command.Module):

    def __init__(self, necrobot, db_connection):
        self._necrobot = necrobot
        self._db_conn = db_connection
        self._results_channel = necrobot.find_channel(config.RACE_RESULTS_CHANNEL_NAME)
        self._racerooms = []
        self.command_types = [Make(self)] #TODO add makeprivate

    @property
    def client(self):
        return self._necrobot.client

    @property
    def main_channel(self):
        return self._necrobot.main_channel

    @property
    def results_channel(self):
        return self._results_channel

    @property
    def prefs(self):
        return self._necrobot.prefs

    @property
    def admin_roles(self):
        return self._necrobot.admin_roles

    ## TODO use more unique names so hope to avoid Spot's cacheing on tablet problem
    ## Return a new (unique) race room name from the race info
    def get_raceroom_name(self, race_info):
        counter = 0
        trial_name = ''
        while True:
            counter += 1
            trial_name = '{0}_{1}'.format(race_info.raceroom_name(), counter)
            name_is_ok = True
            for c in self._necrobot.server.channels:
                if c.name == trial_name:
                    name_is_ok = False

            if name_is_ok:
                return trial_name

    ## Make a race with the given RaceInfo
    @asyncio.coroutine
    def make_race(self, race_info, creator=None, mention=[], suppress_alerts=False):
        #Garbage collect closed race rooms
        self._racerooms = [r for r in self._racerooms if not r.is_closed]
        
        #Make a channel for the race
        race_channel = yield from self.client.create_channel(self._necrobot.server, self.get_raceroom_name(race_info), type='text')

        if race_channel:
            # Make the actual RaceRoom and initialize it 
            new_race = raceroom.RaceRoom(self, race_channel, race_info)
            new_race.creator = creator
            self._racerooms.append(new_race)
            asyncio.ensure_future(new_race.initialize(mention))

            # Send PM alerts
            if not suppress_alerts:
                all_alert_pref = userprefs.UserPrefs()
                all_alert_pref.race_alert = userprefs.RaceAlerts['all']
                alert_string = 'A new race has been started:\nFormat: {1}\nChannel: {0}'.format(race_channel.mention, race_info.format_str())
                for user in self.prefs.get_all_matching(all_alert_pref):
                    asyncio.ensure_future(self.client.send_message(user, alert_string))
        
        return race_channel

    ## Make a private race with the given RaceInfo
    @asyncio.coroutine
    def make_private_race(self, race_private_info, creator=None):
        #Garbage collect closed race rooms
        self._racerooms = [r for r in self._racerooms if not r.is_closed]
        
        #Make the new race
        race_channel = yield from self.client.create_channel(self._necrobot.server, self.get_raceroom_name(race_private_info.race_info), type='text')
        new_race = raceprivateroom.RacePrivateRoom(self, race_channel, race_private_info)
        new_race.creator = creator
        self._racerooms.append(new_race)
        asyncio.ensure_future(new_race.initialize())
        return race_channel

    # Attempts to execute the given command (if a command of its type is in command_types)
    # Overrides
    @asyncio.coroutine
    def execute(self, command):
        for cmd_type in self.command_types:
            yield from cmd_type.execute(command)
        for room in self._racerooms:
            if command.channel == room.channel:
                yield from room.execute(command)

##    ## Move this functionality into RaceRoom / RacePrivateRoom modules (no reason to have this method here; they have access to client) 
##    ## Post a race result in the results channel
##    @asyncio.coroutine
##    def post_result(self, text):
##        if self._results_channel:
##            asyncio.ensure_future(self.client.send_message(self._results_channel, text))
##
##    ## Move into RaceRoom / RacePrivateRoom modules
##    ## Write something to the main channel
##    ## TODO: currently this is called by raceroom, when doing the .rematch command, to announce a rematch
##    ## in the bot's main channel. I think its existence suggests some code refactoring should be done around here;
##    ## in particular, perhaps this class should be more responsible for messages in the main channel regarding races
##    ## at all, and Necrobot should not. One could think of Necrobot as a general structure that takes 'modules', of
##    ## which I've coded a race module and a daily module. This seems like a good refactoring.
##    @asyncio.coroutine
##    def write_in_main(self, text):
##        main_channel = None
##        for channel in self._server.channels:
##            if channel.name == config.MAIN_CHANNEL_NAME:
##                main_channel = channel
##        if main_channel:
##            asyncio.ensure_future(self.client.send_message(main_channel, text))
