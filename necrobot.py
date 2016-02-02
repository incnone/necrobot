import asyncio
import discord
import seedgen
import sqlite3

import config
import command
import colorer

from adminmodule import AdminModule
from userprefs import PrefsModule

class Necrobot(object):

    ## Barebones constructor
    def __init__(self, client, db_conn):
        self.client = client
        self.server = None
        self.prefs = None
        self.modules = []
        self.admin_id = None
        self.db_conn = db_conn
        self._main_channel = None
        self._wants_to_quit = False

    ## Initializes object; call after client has been logged in to discord
    def post_login_init(self, server_id, admin_id=0):
        self.admin_id = admin_id if admin_id else None
       
        #set up server
        id_is_int = False
        try:
            server_id_int = int(server_id)
            id_is_int = True
        except ValueError:
            id_is_int = False
            
        if self.client.servers:
            for s in self.client.servers:
                if id_is_int and s.id == server_id:
                    print("Server id: {}".format(s.id))
                    self.server = s
                elif s.name == server_id:
                    print("Server id: {}".format(s.id))
                    self.server = s
        else:
            print('Error: Could not find the server.')
            exit(1)

        self._main_channel = self.find_channel(config.MAIN_CHANNEL_NAME)
        self.load_module(AdminModule(self))
        self.prefs = PrefsModule(self, self.db_conn)
        self.load_module(self.prefs)

    # Causes the Necrobot to use the given module
    # Doesn't check for duplicates
    def load_module(self, module):
        self.modules.append(module)

    # True if the bot wants to quit (and not re-login)
    @property
    def quitting(self):
        return self._wants_to_quit

    # Return the #necrobot_main channel
    @property
    def main_channel(self):
        return self._main_channel

    # Return the #command_list channel
    @property
    def ref_channel(self):
        for channel in self.server.channels:
            if channel.name == config.REFERENCE_CHANNEL_NAME:
                return channel
        return None

    ## Get a list of all admin roles on the server
    @property
    def admin_roles(self):
        admin_roles = []
        for rolename in config.ADMIN_ROLE_NAMES:
            for role in self.server.roles:
                if role.name == rolename:
                    admin_roles.append(role)
        return admin_roles

    # Returns true if the user is a server admin
    def is_admin(self, user):
        member = self.get_as_member(user)
        admin_roles = self.admin_roles
        for role in member.roles:
            if role in admin_roles:
                return True
        return False

    # Returns the channel with the given name on the server, if any
    def find_channel(self, channel_name):
        for channel in self.server.channels:
            if channel.name == channel_name:
                return channel
        return None

    ## Returns a list of all members with a given username (capitalization ignored)
    def find_members(self, username):
        to_return = []
        for member in self.server.members:
            if member.name == username:
                to_return.append(member)
        return to_return

    ## Log out of discord
    @asyncio.coroutine
    def logout(self):
        self._wants_to_quit = True
        yield from self.client.logout()

    ## Reboot our login to discord (log out, but do not set quitting = true)
    @asyncio.coroutine
    def reboot(self):
        self._wants_to_quit = False
        yield from self.client.logout()

    @asyncio.coroutine
    def execute(self, cmd):
        # don't care about bad commands
        if cmd.command == None:
            return
        
        # don't reply to self
        if cmd.author == self.client.user:
            return

        # only reply on-server or to PM
        if not cmd.is_private and cmd.server != self.server:
            return

        # let each module attempt to handle the command in turn
        for module in self.modules:
            asyncio.ensure_future(module.execute(cmd))

    # Returns the given Discord User as a Member of the server
    def get_as_member(self, user):
        for member in self.server.members:
            if member.id == user.id:
                return member

##    @asyncio.coroutine
##    def main_channel_command(self, message):
##        args = message.content.split()
##        command = args.pop(0).replace(config.BOT_COMMAND_PREFIX, '', 1)
##
##        #.die (super-admin only) : Clean up and log out
##        if command == 'die' and message.author.id == self._admin_id:
##            yield from self.logout()
##
##        #.updatedaily (super-admin only) : Update the daily leaderboard (for debugging)
##        elif command == 'updatedaily' and message.author.id == self._admin_id:
##            asyncio.ensure_future(self._daily_manager.update_leaderboard(self._daily_manager.today_number()))
##
##        #.dankify command : dankify
##        elif command == 'dankify':
##            asyncio.ensure_future(self._dankify_user(message))
##
##        #.help : Quick help reference
##        elif command == 'help':
##            cmd = args[0].lstrip(config.BOT_COMMAND_PREFIX) if len(args) == 1 else ''
##            if cmd in HELP_INFO:
##                asyncio.ensure_future(self.client.send_message(message.channel, HELP_INFO[cmd]))
##            else:
##                ref_channel = None
##                for channel in self.server.channels:
##                    if channel.name == config.REFERENCE_CHANNEL_NAME:
##                        ref_channel = channel
##                if ref_channel:
##                    asyncio.ensure_future(self.client.send_message(message.channel,
##                        "See {} for a command list. Type `.help command` for more info on a particular command.".format(ref_channel.mention)))      
##
##        #.dailyresubmit : Submit a result for your most recently registered daily (if possible)
##        elif command == 'dailyresubmit':
##            spoilerchat_channel = None
##            for channel in self.server.channels:
##                if channel.name == config.DAILY_SPOILERCHAT_CHANNEL_NAME:
##                    spoilerchat_channel = channel
##            if spoilerchat_channel:
##                asyncio.ensure_future(self.client.send_message(message.channel,
##                    "{0}: Please call `.dailyresubmit` from {1} (this helps avoid spoilers in the main channel).".format(message.author.mention, spoilerchat_channel.mention)))      
##                asyncio.ensure_future(self.client.delete_message(message))
##
##        #.dailyrules: Output the rules for the daily
##        elif command == 'dailyrules':
##            yield from self.get_dailyrules(message.channel)
##
##        #.dailyseed : Receive (via PM) today's daily seed
##        elif command == 'dailyseed':
##            yield from self.try_daily_getseed(message.channel, message.author, args)
##
##        #.dailystatus : Get your current status for the current daily (unregistered, registered, can still submit for yesterday, submitted)
##        elif command == 'dailystatus':
##            status = ''        
##            dm = self._daily_manager
##            user_id = message.author.id
##            daily_number = dm.registered_daily(user_id)
##            days_since_registering = dm.today_number() - daily_number
##            submitted = dm.has_submitted(daily_number, user_id)
##
##            if days_since_registering == 1 and not submitted and dm.within_grace_period():
##                status = "You have not gotten today's seed. You may still submit for yesterday's daily, which is open for another {0}.".format(dm.daily_grace_timestr())
##            elif days_since_registering != 0:
##                status = "You have not yet registered: Use `.dailyseed` to get today's seed."
##            elif submitted:
##                status = "You have submitted to the daily. The next daily opens in {0}.".format(dm.next_daily_timestr())
##            else:
##                status = "You have not yet submitted to the daily: Use `.dailysubmit` to submit a result. Today's daily is open for another {0}.".format(dm.daily_close_timestr())
##
##            asyncio.ensure_future(self.client.send_message(message.channel, '{0}: {1}'.format(message.author.mention, status)))        
##    
##        #.dailysubmit : Submit a result for your most recently registered daily (if possible)
##        elif command == 'dailysubmit':
##            spoilerchat_channel = None
##            for channel in self.server.channels:
##                if channel.name == config.DAILY_SPOILERCHAT_CHANNEL_NAME:
##                    spoilerchat_channel = channel
##            if spoilerchat_channel:
##                asyncio.ensure_future(self.client.send_message(message.channel,
##                    "{0}: Please call `.dailysubmit` from {1}, or via PM (this helps avoid spoilers in the main channel).".format(message.author.mention, spoilerchat_channel.mention)))      
##                asyncio.ensure_future(self.client.delete_message(message))
##
##        #.dailyunsubmit : Remove your most recent daily submission (if possible)
##        elif command == 'dailyunsubmit':
##            yield from self.try_daily_unsubmit(message.channel, message.author)     
##        
##        #.dailywhen : Gives time info re the daily
##        elif command == 'dailywhen':
##            info_str = self._daily_manager.daily_time_info_str()
##            asyncio.ensure_future(self.client.send_message(message.channel, info_str))
##
##        #.make : create a new race room
##        elif command == 'make':
##            race_info = raceinfo.parse_args(args)
##            if race_info:
##                race_channel = yield from self._race_manager.make_race(race_info)
##                if race_channel:
##                    alert_string = 'A new race has been started:\nFormat: {1}\nChannel: {0}'.format(race_channel.mention, race_info.format_str())
##                    main_channel_string = 'A new race has been started by {0}:\nFormat: {2}\nChannel: {1}'.format(message.author.mention, race_channel.mention, race_info.format_str())
##
##                    # send PM alerts
##                    some_alert_pref = userprefs.UserPrefs()
##                    some_alert_pref.race_alert = userprefs.RaceAlerts['some']
##                    for user in self.prefs.get_all_matching(some_alert_pref):
##                        asyncio.ensure_future(self.client.send_message(user, alert_string))
##
##                    # alert in main channel
##                    asyncio.ensure_future(self.client.send_message(message.channel, main_channel_string))
##
##        #.makeprivate : create a new race room
##        elif command == 'makeprivate':
##            race_private_info = raceprivateinfo.parse_args(args)
##            if not message.author.name in race_private_info.admin_names:
##                race_private_info.admin_names.append(message.author.name)
##            if race_private_info:
##                race_channel = yield from self._race_manager.make_private_race(race_private_info)
##                if race_channel:
##                    asyncio.ensure_future(self.client.send_message(message.channel,
##                        'A private race has been started by {0}:\nFormat: {2}\nChannel: {1}'.format(message.author.mention, race_channel.mention, race_private_info.race_info.format_str()))) 
##        
##        #.randomseed : Generate a new random seed
##        elif command == 'randomseed':
##            seed = seedgen.get_new_seed()
##            asyncio.ensure_future(self.client.send_message(message.channel, 'Seed generated for {0}: {1}'.format(message.author.mention, seed)))       
##
##        #.setprefs : Set user preferences
##        elif command == 'setprefs':
##            prefs = userprefs.parse_args(args)
##            if prefs.contains_info:
##                self.prefs.set_prefs(prefs, message.author)
##                yield from self._when_updated_prefs(prefs, message.author)
##                confirm_msg = 'Set the following preferences for {}:'.format(message.author.mention)
##                for pref_str in prefs.pref_strings:
##                    confirm_msg += ' ' + pref_str
##                asyncio.ensure_future(self.client.send_message(message.channel, confirm_msg))                 
##            else:
##                asyncio.ensure_future(self.client.send_message(message.channel, '{0}: Failure parsing arguments; did not set any user preferences.'.format(message.author.mention)))                 
##
##        #.info : Bot version information
##        elif command == 'info':
##            ref_channel = None
##            for channel in self.server.channels:
##                if channel.name == config.REFERENCE_CHANNEL_NAME:
##                    ref_channel = channel
##            if ref_channel:
##                asyncio.ensure_future(self.client.send_message(message.channel, 'Necrobot v-{0} (alpha). See {1} for a list of commands.'.format(config.BOT_VERSION, ref_channel.mention)))
##
##    @asyncio.coroutine
##    def daily_spoilerchat_channel_command(self, message):
##        args = message.content.split()
##        command = args.pop(0).replace(config.BOT_COMMAND_PREFIX, '', 1)
##
##        #.dailyresubmit : Correct your most recent daily submission
##        if command == 'dailyresubmit':
##            dm = self._daily_manager
##            user_id = message.author.id
##            daily_number = dm.submitted_daily(user_id)
##
##            if daily_number == 0:
##                asyncio.ensure_future(self.client.send_message(message.channel,
##                    "{0}: You've never submitted for a daily.".format(message.author.mention)))
##            elif not dm.is_open(daily_number):
##                asyncio.ensure_future(self.client.send_message(message.channel,
##                    "{0}: The {1} daily has closed.".format(message.author.mention, daily.daily_to_shortstr(daily_number))))
##            else:
##                submission_string = dm.parse_submission(daily_number, message.author, args, overwrite=True)
##                if submission_string: # parse succeeded
##                    asyncio.ensure_future(self.client.send_message(message.channel,
##                        "Resubmitted for {0}: {1} {2}.".format(daily.daily_to_shortstr(daily_number), message.author.mention, submission_string)))
##                    asyncio.ensure_future(dm.update_leaderboard(daily_number))
##                else: # parse failed
##                    asyncio.ensure_future(self.client.send_message(message.channel,
##                        "{0}: I had trouble parsing your submission. Please use one of the forms: `.dailysubmit 12:34.56` or `.dailysubmit death 4-4`.".format(message.author.mention)))
##               
##        #.dailysubmit : Submit a time for today's daily
##        elif command == 'dailysubmit':
##            yield from self.try_daily_submit(message.channel, message.author, args)
##
##        elif command == 'dailyunsubmit':
##            yield from self.try_daily_unsubmit(message.channel, message.author)
##
##    # Tries to un-submit the daily of the message author, if possible, and output reasonable messages
##    @asyncio.coroutine
##    def try_daily_unsubmit(self, channel, user):
##        dm = self._daily_manager
##        daily_number = dm.submitted_daily(user.id)
##
##        if daily_number == 0:
##            asyncio.ensure_future(self.client.send_message(channel,
##                "{0}: You've never submitted for a daily.".format(user.mention)))
##        elif not dm.is_open(daily_number):
##            asyncio.ensure_future(self.client.send_message(channel,
##                "{0}: The {1} daily has closed.".format(user.mention, daily.daily_to_shortstr(daily_number))))
##        else:
##            dm.delete_from_daily(daily_number, user)
##            asyncio.ensure_future(self.client.send_message(channel,
##                "Deleted {1}'s daily submission for {0}.".format(daily.daily_to_shortstr(daily_number), user.mention)))
##            asyncio.ensure_future(dm.update_leaderboard(daily_number))
##
##    #Try to get today's daily seed if possible
##    @asyncio.coroutine
##    def try_daily_getseed(self, channel, member, args):
##        dm = self._daily_manager
##        user_id = member.id
##        
##        today = dm.today_number()
##        today_date = daily.daily_to_date(today)
##        if dm.has_submitted(today, user_id):
##            asyncio.ensure_future(self.client.send_message(channel, "{0}: You have already submitted for today's daily.".format(member.mention)))
##        elif dm.within_grace_period() and dm.has_registered(today - 1, user_id) and not dm.has_submitted(today - 1, user_id) and not (len(args) == 1 and args[0].lstrip('-') == 'override'):
##                asyncio.ensure_future(self.client.send_message(member, "{0}: Warning: You have not yet " \
##                    "submitted for yesterday's daily, which is open for another {1}. If you want to forfeit the " \
##                    "ability to submit for yesterday's daily and get today's seed, call `.dailyseed -override`.".format(member.mention, dm.daily_grace_timestr())))                
##        else:
##            dm.register(today, user_id)
##            seed = yield from dm.get_seed(today)
##            asyncio.ensure_future(self.client.send_message(member, "({0}) Today's Cadence speedrun seed: {1}. " \
##                "This is a single-attempt Cadence seeded all zones run. (See `.dailyrules` for complete rules.)".format(today_date.strftime("%d %b"), seed)))     
##
##    #Output the rules for the daily
##    @asyncio.coroutine
##    def get_dailyrules(self, channel):
##        asyncio.ensure_future(self.client.send_message(channel, "Rules for the speedrun daily:\n" \
##            "\N{BULLET} Cadence seeded all zones; get the seed for the daily using `.dailyseed`.\n" \
##            "\N{BULLET} Run the seed blind. Make one attempt and submit the result (even if you die).\n" \
##            "\N{BULLET} No restriction on resolution, display settings, zoom, etc.\n" \
##            "\N{BULLET} Mods that disable leaderboard submission are not allowed (e.g. xml / music mods)."))                                             
##
##    #Try to submit a daily by the message author, if possible, and output reasonable messages
##    @asyncio.coroutine
##    def try_daily_submit(self, channel, user, args):
##        dm = self._daily_manager
##        daily_number = dm.registered_daily(user.id)
##
##        if daily_number == 0:
##            asyncio.ensure_future(self.client.send_message(channel,
##                "{0}: Please get today's daily seed before submitting (use `.dailyseed`).".format(user.mention, daily.daily_to_shortstr(daily_number))))
##        elif not dm.is_open(daily_number):
##            asyncio.ensure_future(self.client.send_message(channel,
##                "{0}: Too late to submit for the {1} daily. Get today's seed with `.dailyseed`.".format(user.mention, daily.daily_to_shortstr(daily_number))))
##        elif dm.has_submitted(daily_number, user.id):
##            asyncio.ensure_future(self.client.send_message(channel,
##                "{0}: You have already submitted for the {1} daily.".format(user.mention, daily.daily_to_shortstr(daily_number))))
##        else:
##            submission_string = dm.parse_submission(daily_number, user, args)
##            if submission_string: # parse succeeded
##                if channel.is_private: # submitted through pm
##                    asyncio.ensure_future(self.client.send_message(channel,
##                        "Submitted for {0}: You {1}.".format(daily.daily_to_shortstr(daily_number), submission_string)))
##                if dm._spoilerchat_channel:
##                    asyncio.ensure_future(self.client.send_message(dm._spoilerchat_channel,
##                        "Submitted for {0}: {1} {2}.".format(daily.daily_to_shortstr(daily_number), user.mention, submission_string)))
##                asyncio.ensure_future(dm.update_leaderboard(daily_number))
##            else: # parse failed
##                asyncio.ensure_future(self.client.send_message(channel,
##                    "{0}: I had trouble parsing your submission. Please use one of the forms: `.dailysubmit 12:34.56` or `.dailysubmit death 4-4`.".format(user.mention)))
##
##    @asyncio.coroutine
##    def _dankify_user(self, message):
##        asyncio.ensure_future(colorer.color_user(message.author, self.client, self.server))
##        #yield from asyncio.sleep(1)
##        asyncio.ensure_future(self.client.delete_message(message))
##
