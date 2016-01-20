#TODO: maybe a command to .dailyseed should not register for the new daily if you've yet to complete old one?

import asyncio
import discord
import seedgen
import sqlite3

import daily
import racemgr
import raceinfo
import raceprivateinfo

import config

HELP_INFO = {
    "help":"`.help`: Help.",
    "dailyresubmit":"`.dailyresubmit`: Submit for the daily, overriding a previous submission. Use this to correct a mistake in a daily submission.",
    "dailystatus":"`.dailystatus`: Find out whether you've submitted to today's daily.",
    "dailysubmit":"`.dailysubmit`: Submit a result for your most recent daily. Daily submissions close an hour after the next " \
                    "daily opens. If you complete the game during the daily, submit your time in the form [m]:ss.hh, e.g.: " \
                    "`.dailysubmit 12:34.56`. If you die during the daily, you may submit your run as `.dailysubmit death` " \
                    "or provide the level of death, e.g. `.dailysubmit death 4-4` for a death on dead ringer.",
    "dailywhen":"`.dailywhen`: Get the date for the current daily, and the time until the next daily opens.",
    "make":"`.make`: Create a new race room. By default this creates an unseeded Cadence race, " \
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
                    "Finally, desc allows you to give any custom one-word description of the race (e.g., '4-shrine').",
    "makeprivate":"`.makeprivate`: Create a new private race room. This takes the same command-line options as `.make`, as well as " \
                    "a few more:\n" \
                    "```" \
                    ".makeprivate [-a admin...] [-r racer...]" ##[-bestof x | -repeat y]" \
                    "```" \
                    "Here `admin...` is a list of names of 'admins' for the race, which are users that can both see the race channel and " \
                    "use special admin commands for managing the race, and `racer...` is a list of users that can see the race channel. " \
                    "(Both admins and racers can enter the race.)", ##`x` causes the race to become a best-of-x match, and `y` causes it to " \
                    ##"simply repeat the race y times (for instance, CoNDOR s3 had a `-repeat 3` format during the swiss.)",                    
    "randomseed":"`.randomseed`: Get a randomly generated seed.",
    "info":"`.info`: Necrobot version information.",
    }

class Necrobot(object):

    ## Barebones constructor
    def __init__(self, client,):
        self._client = client
        self._server = None
        self._admin_id = None
        self._daily_manager = None
        self._race_manager = None

    ## Initializes object; call after client has been logged in to discord
    def post_login_init(self, server_id, admin_id=None):

        self._admin_id = admin_id if admin_id != 0 else None
        
        #set up server
        id_is_int = False
        try:
            server_id_int = int(server_id)
            id_is_int = True
        except ValueError:
            id_is_int = False
            
        if self._client.servers:
            for s in self._client.servers:
                if id_is_int and s.id == server_id:
                    self._server = s
                elif s.name == server_id:
                    print("Server id: {}".format(s.id))
                    self._server = s
        else:
            print('Error: Could not find the server.')
            exit(1)

        #set up daily manager
        daily_db_connection = sqlite3.connect(config.DAILY_DB_FILENAME)
        self._daily_manager = daily.DailyManager(self._client, daily_db_connection)

        #set up race manager
        race_db_connection = sqlite3.connect(config.RACE_DB_FILENAME)
        self._race_manager = racemgr.RaceManager(self._client, self._server, race_db_connection)

    ## Log out of discord
    @asyncio.coroutine
    def logout(self):
        yield from self._client.logout()       

    @asyncio.coroutine
    def parse_message(self, message):
        # don't reply to self
        if message.author == self._client.user:
            return

        # don't reply off server
        if not message.server == self._server:
            return

        # check for command prefix
        if not message.content.startswith(config.BOT_COMMAND_PREFIX):
            return

        # parse the command, depending on the channel it was typed in (this just restricts which commands are available from where)
        if message.channel.name == config.MAIN_CHANNEL_NAME:
            yield from self.main_channel_command(message)
        elif message.channel.name == config.DAILY_SPOILERCHAT_CHANNEL_NAME:
            yield from self.daily_spoilerchat_channel_command(message)
        else:
            yield from self._race_manager.parse_message(message)

    @asyncio.coroutine
    def main_channel_command(self, message):
        args = message.content.split()
        command = args.pop(0).replace(config.BOT_COMMAND_PREFIX, '', 1)

        #.die (super-admin only) : Clean up and log out
        if command == 'die' and message.author.id == self._admin_id:
            yield from self.logout()

        #.updatedaily (super-admin only) : Update the daily leaderboard (for debugging)
        elif command == 'updatedaily' and message.author.id == self._admin_id:
            asyncio.ensure_future(self._daily_manager.update_leaderboard(self._daily_manager.today_number()))

        #.help : Quick help reference
        elif command == 'help':
            if len(args) == 1:
                cmd = args[0].lstrip(config.BOT_COMMAND_PREFIX)
                if cmd in HELP_INFO:
                    asyncio.ensure_future(self._client.send_message(message.channel, HELP_INFO[cmd]))
            else:
                ref_channel = None
                for channel in self._server.channels:
                    if channel.name == config.REFERENCE_CHANNEL_NAME:
                        ref_channel = channel
                if ref_channel:
                    asyncio.ensure_future(self._client.send_message(message.channel,
                        "See {} for a command list. Type `.help command` for more info on a particular command.".format(ref_channel.mention)))      

        #.dailyresubmit : Submit a result for your most recently registered daily (if possible)
        elif command == 'dailyresubmit':
            spoilerchat_channel = None
            for channel in self._server.channels:
                if channel.name == config.DAILY_SPOILERCHAT_CHANNEL_NAME:
                    spoilerchat_channel = channel
            if spoilerchat_channel:
                asyncio.ensure_future(self._client.send_message(message.channel,
                    "{0}: Please call `.dailyresubmit` from {1} (this helps avoid spoilers in the main channel).".format(message.author.mention, spoilerchat_channel.mention)))      
                asyncio.ensure_future(self._client.delete_message(message))

        #.dailyseed : Receive (via PM) today's daily seed
        elif command == 'dailyseed':
            dm = self._daily_manager
            user_id = message.author.id
            
            today = dm.today_number()
            today_date = daily.daily_to_date(today)
            if dm.has_submitted(today, user_id):
                asyncio.ensure_future(self._client.send_message(message.channel, "{0}: You have already submitted for today's daily.".format(message.author.mention)))
            elif dm.within_grace_period() and dm.has_registered(today - 1, user_id) and not dm.has_submitted(today - 1, user_id) and not (len(args) == 1 and args[0].lstrip('-') == 'override'):
                    asyncio.ensure_future(self._client.send_message(message.author, "{0}: Warning: You have not yet " \
                        "submitted for yesterday's daily, which is open for another {1}. If you want to forfeit the " \
                        "ability to submit for yesterday's daily and get today's seed, call `.dailyseed -override`.".format(message.author.mention, dm.daily_grace_timestr())))                
            else:
                dm.register(today, user_id)
                seed = yield from dm.get_seed(today)
                asyncio.ensure_future(self._client.send_message(message.author, "({0}) Today's Cadence speedrun seed: {1}".format(today_date.strftime("%d %b"), seed)))

        #.dailystatus : Get your current status for the current daily (unregistered, registered, can still submit for yesterday, submitted)
        elif command == 'dailystatus':
            status = ''        
            dm = self._daily_manager
            user_id = message.author.id
            daily_number = dm.registered_daily(user_id)
            days_since_registering = dm.today_number() - daily_number
            submitted = dm.has_submitted(daily_number, user_id)

            if days_since_registering == 1 and not submitted and dm.within_grace_period():
                status = "You have not gotten today's seed. You may still submit for yesterday's daily, which is open for another {0}.".format(dm.daily_grace_timestr())
            elif days_since_registering != 0:
                status = "You have not yet registered: Use `.dailyseed` to get today's seed."
            elif submitted:
                status = "You have submitted to the daily. The next daily opens in {0}.".format(dm.next_daily_timestr())
            else:
                status = "You have not yet submitted to the daily: Use `.dailysubmit` to submit a result. Today's daily is open for another {0}.".format(dm.daily_close_timestr())

            asyncio.ensure_future(self._client.send_message(message.channel, '{0}: {1}'.format(message.author.mention, status)))        
    
        #.dailysubmit : Submit a result for your most recently registered daily (if possible)
        elif command == 'dailysubmit':
            spoilerchat_channel = None
            for channel in self._server.channels:
                if channel.name == config.DAILY_SPOILERCHAT_CHANNEL_NAME:
                    spoilerchat_channel = channel
            if spoilerchat_channel:
                asyncio.ensure_future(self._client.send_message(message.channel,
                    "{0}: Please call `.dailysubmit` from {1} (this helps avoid spoilers in the main channel).".format(message.author.mention, spoilerchat_channel.mention)))      
                asyncio.ensure_future(self._client.delete_message(message))
        
        #.dailywhen : Gives time info re the daily
        elif command == 'dailywhen':
            info_str = self._daily_manager.daily_time_info_str()
            asyncio.ensure_future(self._client.send_message(message.channel, info_str))

        #.make : create a new race room
        elif command == 'make':
            race_info = raceinfo.parse_args(args)
            if race_info:
                race_channel = yield from self._race_manager.make_race(race_info)
                if race_channel:
                    asyncio.ensure_future(self._client.send_message(message.channel,
                        'A new race has been started by {0}:\nFormat: {2}\nChannel: {1}'.format(message.author.mention, race_channel.mention, race_info.format_str())))

        #.makeprivate : create a new race room
        elif command == 'makeprivate':
            race_private_info = raceprivateinfo.parse_args(args)
            if not message.author.name in race_private_info.admin_names:
                race_private_info.admin_names.append(message.author.name)
            if race_private_info:
                race_channel = yield from self._race_manager.make_private_race(race_private_info)
                if race_channel:
                    asyncio.ensure_future(self._client.send_message(message.channel,
                        'A private race has been started by {0}:\nFormat: {2}\nChannel: {1}'.format(message.author.mention, race_channel.mention, race_private_info.race_info.format_str()))) 
        
        #.randomseed : Generate a new random seed
        elif command == 'randomseed':
            seed = seedgen.get_new_seed()
            asyncio.ensure_future(self._client.send_message(message.channel, 'Seed generated for {0}: {1}'.format(message.author.mention, seed)))       

        elif command == 'info':
            ref_channel = None
            for channel in self._server.channels:
                if channel.name == config.REFERENCE_CHANNEL_NAME:
                    ref_channel = channel
            if ref_channel:
                asyncio.ensure_future(self._client.send_message(message.channel, 'Necrobot v-{0} (alpha). See {1} for a list of commands.'.format(config.BOT_VERSION, ref_channel.mention)))

    @asyncio.coroutine
    def daily_spoilerchat_channel_command(self, message):
        args = message.content.split()
        command = args.pop(0).replace(config.BOT_COMMAND_PREFIX, '', 1)

        #.dailyresubmit : Correct your most recent daily submission
        if command == 'dailyresubmit':
            dm = self._daily_manager
            user_id = message.author.id
            daily_number = dm.submitted_daily(user_id)

            if daily_number == 0:
                asyncio.ensure_future(self._client.send_message(message.channel,
                    "{0}: You've never submitted for a daily.".format(message.author.mention)))
            elif not dm.is_open(daily_number):
                asyncio.ensure_future(self._client.send_message(message.channel,
                    "{0}: The {1} daily has closed.".format(message.author.mention, daily.daily_to_shortstr(daily_number))))
            else:
                submission_string = dm.parse_submission(daily_number, message.author, args, overwrite=True)
                if submission_string: # parse succeeded
                    asyncio.ensure_future(self._client.send_message(message.channel,
                        "Resubmitted for {0}: {1} {2}.".format(daily.daily_to_shortstr(daily_number), message.author.mention, submission_string)))
                    asyncio.ensure_future(dm.update_leaderboard(daily_number))
                else: # parse failed
                    asyncio.ensure_future(self._client.send_message(message.channel,
                        "{0}: I had trouble parsing your submission. Please use one of the forms: `.dailysubmit 12:34.56` or `.dailysubmit death 4-4`.".format(message.author.mention)))
               
        #.dailysubmit : Submit a time for today's daily
        if command == 'dailysubmit':
            dm = self._daily_manager
            user_id = message.author.id
            daily_number = dm.registered_daily(user_id)

            if daily_number == 0:
                asyncio.ensure_future(self._client.send_message(message.channel,
                    "{0}: Please get today's daily seed before submitting (use `.dailyseed`).".format(message.author.mention, daily.daily_to_shortstr(daily_number))))
            elif not dm.is_open(daily_number):
                asyncio.ensure_future(self._client.send_message(message.channel,
                    "{0}: Too late to submit for the {1} daily. Get today's seed with `.dailyseed`.".format(message.author.mention, daily.daily_to_shortstr(daily_number))))
            elif dm.has_submitted(daily_number, user_id):
                asyncio.ensure_future(self._client.send_message(message.channel,
                    "{0}: You have already submitted for the {1} daily.".format(message.author.mention, daily.daily_to_shortstr(daily_number))))
            else:
                submission_string = dm.parse_submission(daily_number, message.author, args)
                if submission_string: # parse succeeded
                    asyncio.ensure_future(self._client.send_message(message.channel,
                        "Submitted for {0}: {1} {2}.".format(daily.daily_to_shortstr(daily_number), message.author.mention, submission_string)))
                    asyncio.ensure_future(dm.update_leaderboard(daily_number))
                else: # parse failed
                    asyncio.ensure_future(self._client.send_message(message.channel,
                        "{0}: I had trouble parsing your submission. Please use one of the forms: `.dailysubmit 12:34.56` or `.dailysubmit death 4-4`.".format(message.author.mention)))

