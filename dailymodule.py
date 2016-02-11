import asyncio
import calendar
import datetime
import discord

import command
import config
import daily
import dailytype
import userprefs

class DailyCommandType(command.CommandType):
    def __init__(self, daily_module, *args, **kwargs):
        command.CommandType.__init__(self, *args, **kwargs)
        self._dm = daily_module

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._dm.main_channel or self._dm.is_spoilerchat_channel(channel)
        
    @asyncio.coroutine
    def _do_execute(self, command):
        today_number = self._dm.today_number
        called_type = dailytype.parse_out_type(command, today_number)

        if not called_type.explicit_char and self._dm.is_spoilerchat_channel(command.channel):
            called_type = self._dm.get_type_for_spoilerchat(command.channel)

        if called_type:
            yield from self._daily_do_execute(command, called_type)
        else:
            asyncio.ensure_future(self._dm.client.send_message(command.channel,
                "{0}: I couldn't figure out which daily you wanted to call a command for.".format(command.author.mention)))              

    @asyncio.coroutine
    def _daily_do_execute(self, command, called_type):
        print('Error: _daily_do_execute not overridden in base.')

class DailyChar(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailychar', 'dailywho')
        self.help_text = 'Get the character for the current rotating-character daily.'

    @asyncio.coroutine
    def _daily_do_execute(self, command, called_type):
        manager = self._dm.daily(dailytype.RotatingSpeed())
        character = dailytype.RotatingSpeed().character(manager.today_number)
        asyncio.ensure_future(self._dm.client.send_message(command.channel, 'Today\'s character is {0}.'.format(character)))

class DailyResubmit(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailyresubmit')
        self.help_text = 'Submit for the Cadence daily, overriding a previous submission. Use this to correct a mistake in a daily submission. ' \
                         'Use the `-rot` flag to resubmit for the rotating-character daily.'

    @asyncio.coroutine
    def _daily_do_execute(self, command, called_type):       
        client = self._dm.client
        manager = self._dm.daily(called_type.type)
        
        # Command sent via PM or in #dailyspoilerchat
        if command.is_private or command.channel == manager.spoilerchat_channel:
            
            last_submitted = manager.submitted_daily(command.author.id)
            character = called_type.type.character(last_submitted)

            if last_submitted == 0:
                asyncio.ensure_future(client.send_message(command.channel,
                    "{0}: You've never submitted for a daily of this type.".format(command.author.mention)))
            elif not manager.is_open(last_submitted):
                asyncio.ensure_future(client.send_message(command.channel,
                    "{0}: The {1} {2} daily has closed.".format(command.author.mention, daily.daily_to_shortstr(last_submitted), character)))
            else:
                submission_string = manager.parse_submission(last_submitted, command.author, command.args)
                if submission_string: # parse succeeded
                    # Respond in PM if submission is in PM
                    if command.is_private:
                        asyncio.ensure_future(client.send_message(command.channel,
                            "Reubmitted for {0}, {2}: You {1}.".format(daily.daily_to_shortstr(last_submitted), submission_string, character)))

                    # Post to spoilerchat (regardless of where submission was)
                    asyncio.ensure_future(client.send_message(manager.spoilerchat_channel,
                        "Resubmitted for {0}, {3}: {1} {2}.".format(daily.daily_to_shortstr(last_submitted), command.author.mention, submission_string, character)))
                    asyncio.ensure_future(self._dm.update_leaderboard(last_submitted, called_type.type))

                else: # parse failed
                    asyncio.ensure_future(client.send_message(command.channel,
                        "{0}: I had trouble parsing your submission. Please use one of the forms: `{1} 12:34.56` or `{1} death 4-4`.".format(command.author.mention, self.mention)))  

        # Command sent in main channel
        elif command.channel == self._dm.main_channel:
            
            asyncio.ensure_future(client.send_message(command.channel,
                "{0}: Please call `{1}` from {2} (this helps avoid spoilers in the main channel).".format(command.author.mention, self.mention, manager.spoilerchat_channel.mention)))      
            asyncio.ensure_future(client.delete_message(command.message))

class DailyRules(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailyrules')
        self.help_text = 'Get the rules for the speedrun daily.'

    @asyncio.coroutine
    def _daily_do_execute(self, command, called_type):
        character = called_type.character
        client = self._dm.client
        asyncio.ensure_future(client.send_message(command.channel, "Rules for the {0} speedrun daily:\n" \
            "\N{BULLET} {0} seeded all zones; get the seed for the daily using `.dailyseed`.\n" \
            "\N{BULLET} Run the seed blind. Make one attempt and submit the result (even if you die).\n" \
            "\N{BULLET} No restriction on resolution, display settings, zoom, etc.\n" \
            "\N{BULLET} Mods that disable leaderboard submission are not allowed (e.g. xml / music mods).".format(character))) 

class DailySchedule(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailyschedule')
        self.help_text = 'See the scheduled characters for the next few days.'

    @asyncio.coroutine
    def _daily_do_execute(self, command, called_type):
        char_list_str = ''
        today_number = self._dm.daily(dailytype.RotatingSpeed()).today_number
        today_char = dailytype.RotatingSpeed().character(today_number)
        char_found = False
        for charname in dailytype.RotatingSpeed().rotating_chars:
            if charname == today_char:
                char_found = True
            if char_found:
                char_list_str += charname + ' -- '
        for charname in dailytype.RotatingSpeed().rotating_chars:
            if charname == today_char:
                break
            else:
                char_list_str += charname + ' -- '
        char_list_str = char_list_str[:-4]
        asyncio.ensure_future(self._dm.client.send_message(command.channel, 'Upcoming characters, starting today: {0}.'.format(char_list_str)))

class DailySeed(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailyseed')
        self.help_text = 'Get the seed for today\'s Cadence daily. Use the `-rot` flag to get the rotating-character daily seed.'

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._dm.main_channel

    @asyncio.coroutine
    def _daily_do_execute(self, command, called_type):
        client = self._dm.client
        manager = self._dm.daily(called_type.type)
        user_id = command.author.id
        character = called_type.character
        
        today = manager.today_number
        today_date = daily.daily_to_date(today)
        if manager.has_submitted(today, user_id):
            asyncio.ensure_future(client.send_message(command.channel, "{0}: You have already submitted for today's {1} daily.".format(command.author.mention, character)))
        elif manager.within_grace_period() and manager.has_registered(today - 1, user_id) and not manager.has_submitted(today - 1, user_id) and not (len(command.args) == 1 and command.args[0].lstrip('-') == 'override'):
            asyncio.ensure_future(client.send_message(command.author, "{0}: Warning: You have not yet " \
                "submitted for yesterday's {2} daily, which is open for another {1}. If you want to forfeit the " \
                "ability to submit for yesterday's daily and get today's seed, call `.dailyseed -override`.".format(command.author.mention, manager.daily_grace_timestr(), character)))                
        else:
            manager.register(today, user_id)
            seed = manager.get_seed(today)
            asyncio.ensure_future(client.send_message(command.author, "({0}) {2} speedrun seed: {1}. " \
                "This is a single-attempt {2} seeded all zones run. (See `.dailyrules` for complete rules.)".format(today_date.strftime("%d %b"), seed, character)))                                                

class DailyStatus(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailystatus')
        self.help_text = 'Find out whether you\'ve submitted to today\'s Cadence daily. Use the `-rot` flag to get status for the rotating-character daily.'

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._dm.main_channel

    @asyncio.coroutine
    def _daily_do_execute(self, command, called_type):
        client = self._dm.client
        status = ''

        for dtype in self._dm.daily_types:
            manager = self._dm.daily(dtype)
            character = dtype.character(manager.today_number)
            old_char = dtype.character(manager.today_number - 1)
            last_registered = manager.registered_daily(command.author.id)
            days_since_registering = manager.today_number - last_registered
            submitted = manager.has_submitted(last_registered, command.author.id)

            if days_since_registering == 1 and not submitted and manager.within_grace_period():
                status += "You have not gotten today's {1} seed. You may still submit for yesterday's {2} daily, which is open for another {0}. ".format(manager.daily_grace_timestr(), character, old_char)
            elif days_since_registering != 0:
                status += "You have not yet registered for the {0} daily: Use `.dailyseed` to get today's seed. ".format(character)
            elif submitted:
                status += "You have submitted to the {1} daily. The next daily opens in {0}. ".format(manager.next_daily_timestr(), character)
            else:
                status += "You have not yet submitted to the {1} daily: Use `.dailysubmit` to submit a result. Today's {1} daily is open for another {0}. ".format(manager.daily_close_timestr(), character)

        asyncio.ensure_future(client.send_message(command.channel, '{0}: {1}'.format(command.author.mention, status)))        

class DailySubmit(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailysubmit')
        self.help_text = "Submit a result for your most recent Cadence daily (use the `-rot` flag to submit for rotating-character " \
                    "dailies). Daily submissions close an hour after the next " \
                    "daily opens. If you complete the game during the daily, submit your time in the form [m]:ss.hh, e.g.: " \
                    "`.dailysubmit 12:34.56`. If you die during the daily, you may submit your run as `.dailysubmit death` " \
                    "or provide the level of death, e.g. `.dailysubmit death 4-4` for a death on dead ringer. This command can " \
                    "be called in the appropriate spoilerchat or via PM."

    @asyncio.coroutine
    def _daily_do_execute(self, command, called_type):
        client = self._dm.client
        manager = self._dm.daily(called_type.type)    

        # Command sent via PM or in #dailyspoilerchat
        if command.is_private or command.channel == manager.spoilerchat_channel:
            daily_number = manager.registered_daily(command.author.id)
            character = called_type.type.character(daily_number)

            if daily_number == 0:
                asyncio.ensure_future(client.send_message(command.channel,
                    "{0}: Please get today's {1} daily seed before submitting (use `.dailyseed`).".format(command.author.mention, character)))
            elif not manager.is_open(daily_number):
                asyncio.ensure_future(client.send_message(command.channel,
                    "{0}: Too late to submit for the {1} {2} daily. Get today's seed with `.dailyseed`.".format(command.author.mention, daily.daily_to_shortstr(daily_number), character)))
            elif manager.has_submitted(daily_number, command.author.id):
                asyncio.ensure_future(client.send_message(command.channel,
                    "{0}: You have already submitted for the {1} {2} daily. Use `.dailyresubmit` to edit your submission.".format(command.author.mention, daily.daily_to_shortstr(daily_number), character)))
            else:
                submission_string = manager.parse_submission(daily_number, command.author, command.args)
                if submission_string: # parse succeeded

                    # Respond in PM if submission is in PM
                    if command.is_private:
                        asyncio.ensure_future(client.send_message(command.channel,
                            "Submitted for {0}, {2}: You {1}.".format(daily.daily_to_shortstr(daily_number), submission_string, character)))

                    # Post to spoilerchat (regardless of where submission was)
                    asyncio.ensure_future(client.send_message(manager.spoilerchat_channel,
                        "Submitted for {0}, {3}: {1} {2}.".format(daily.daily_to_shortstr(daily_number), command.author.mention, submission_string, character)))
                    asyncio.ensure_future(self._dm.update_leaderboard(daily_number, called_type.type))

                    # If submitting for today, make spoilerchat visible
                    if daily_number == manager.today_number:
                        yield from client.delete_channel_permissions(manager.spoilerchat_channel, self._dm.necrobot.get_as_member(command.author))
                    
                else: # parse failed
                    asyncio.ensure_future(client.send_message(command.channel,
                        "{0}: I had trouble parsing your submission. Please use one of the forms: `{1} 12:34.56` or `{1} death 4-4`.".format(command.author.mention, self.mention)))

        # Command sent in main channel
        elif command.channel == self._dm.main_channel:
            asyncio.ensure_future(client.send_message(command.channel,
                "{0}: Please call `{1}` from {2}, or via PM (this helps avoid spoilers in the main channel).".format(command.author.mention, self.mention, manager.spoilerchat_channel.mention)))      
            asyncio.ensure_future(client.delete_message(command.message))

class DailyUnsubmit(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailyunsubmit')
        self.help_text = 'Retract your most recent Cadence daily submission (only works while the daily is still open). Use the `-rot` flag to unsubmit for the rotating-character daily.'

    @asyncio.coroutine
    def _daily_do_execute(self, command, called_type):
        client = self._dm.client
        manager = self._dm.daily(called_type.type)
        daily_number = manager.submitted_daily(command.author.id)
        character = called_type.type.character(daily_number)

        if daily_number == 0:
            asyncio.ensure_future(client.send_message(command.channel,
                "{0}: You've never submitted for a {1} daily.".format(command.author.mention, character)))
        elif not manager.is_open(daily_number):
            asyncio.ensure_future(client.send_message(command.channel,
                "{0}: The {1} {2} daily has closed.".format(command.author.mention, daily.daily_to_shortstr(daily_number), character)))
        else:
            manager.delete_from_daily(daily_number, command.author)
            asyncio.ensure_future(client.send_message(command.channel,
                "Deleted {1}'s daily submission for {0}, {2}.".format(daily.daily_to_shortstr(daily_number), command.author.mention, character)))
            asyncio.ensure_future(self._dm.update_leaderboard(daily_number, called_type.type))        

class DailyWhen(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailyinfo', 'dailywhen')
        self.help_text = 'Get the date for the current Cadence daily, and the time until the next daily opens. Use the `-rot` flag to get information (including character) for the rotating-character daily.' \
                         'Can also be called with `.dailywhen`. Calling `.dailywhen coda` will tell you when the next Coda daily is (likewise for other characters).'

    @asyncio.coroutine
    def _daily_do_execute(self, command, called_type):
        found_char = False
        for arg in command.args:
            found_char = True
            charname = arg.lstrip('-').capitalize()
            if charname in dailytype.RotatingSpeed().rotating_chars:
                today_number = self._dm.daily(dailytype.RotatingSpeed()).today_number
                days_until = dailytype.RotatingSpeed().days_until(charname, today_number)
                string_to_send = ''
                if days_until == 0:
                    string_to_send = 'The {0} daily is today!'.format(charname)
                elif days_until == 1:
                    string_to_send = 'The {0} daily is tomorrow!'.format(charname)
                elif days_until != None:
                    date = datetime.datetime.utcnow().date() + datetime.timedelta(days=days_until)
                    string_to_send = 'The {0} daily is in {1} days ({2}, {3}).'.format(charname, days_until, calendar.day_name[date.weekday()], date.strftime("%B %d"))
                asyncio.ensure_future(self._dm.client.send_message(command.channel, string_to_send))
        if found_char:
            return
                
        manager = self._dm.daily(called_type.type)
        string_to_send = manager.daily_time_info_str()
        if called_type.type == dailytype.RotatingSpeed():
            string_to_send = 'Today\'s rotating character is {0}. {1}'.format(called_type.character, string_to_send)
        asyncio.ensure_future(self._dm.client.send_message(command.channel, string_to_send))

#For debugging/testing
class ForceRunNewDaily(DailyCommandType): 
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'forcerunnewdaily')
        self.suppress_help = True

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._dm.main_channel

    @asyncio.coroutine
    def _daily_do_execute(self, command, called_type):
        if command.author.id == self._dm.necrobot.admin_id:
            for daily_type in dailytype.all_types:
                yield from self._dm.on_new_daily(self._dm.daily(daily_type))

class ForceUpdateLeaderboard(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'forceupdateleaderboard')
        self.suppress_help = True

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._dm.main_channel

    @asyncio.coroutine
    def _daily_do_execute(self, command, called_type):
        if command.author.id == self._dm.necrobot.admin_id:
            days_back = 0
            show_seed = False
            for arg in command.args:
                if arg.lstrip('-').lower() == 'showseed':
                    show_seed = True
                    
                try:
                    arg_as_int = int(arg)
                    days_back = arg_as_int
                except ValueError:
                    pass

            for daily_type in dailytype.all_types:
                number = self._dm.today_number - days_back
                show_seed = show_seed or days_back > 0
                yield from self._dm.update_leaderboard(number, daily_type, show_seed)

class PublicDaily(daily.Daily):
    def __init__(self, daily_module, db_connection, daily_type):
        daily.Daily.__init__(self, daily_module, db_connection, daily_type)
        self.spoilerchat_channel = None
        self.leaderboard_channel = None

class DailyModule(command.Module):
    def __init__(self, necrobot, db_connection):
        command.Module.__init__(self, necrobot)

        self._cadence_daily = PublicDaily(self, db_connection, dailytype.CadenceSpeed())
        self._cadence_daily.spoilerchat_channel = necrobot.find_channel(config.DAILY_SPOILERCHAT_CHANNEL_NAME)
        self._cadence_daily.leaderboard_channel = necrobot.find_channel(config.DAILY_LEADERBOARDS_CHANNEL_NAME)

        self._rotating_daily = PublicDaily(self, db_connection, dailytype.RotatingSpeed())
        self._rotating_daily.spoilerchat_channel = necrobot.find_channel(config.ROTATING_DAILY_SPOILERCHAT_CHANNEL_NAME)
        self._rotating_daily.leaderboard_channel = necrobot.find_channel(config.ROTATING_DAILY_LEADERBOARDS_CHANNEL_NAME)        

        self.command_types = [command.DefaultHelp(self),
                              DailyChar(self),
                              DailyResubmit(self),
                              DailyRules(self),
                              DailySchedule(self),
                              DailySeed(self),
                              DailyStatus(self),
                              DailySubmit(self),
                              DailyUnsubmit(self),
                              DailyWhen(self),
                              ForceRunNewDaily(self),
                              ForceUpdateLeaderboard(self)]

    @property
    def infostr(self):
        return 'Speedrun daily'

    @property
    def main_channel(self):
        return self.necrobot.main_channel

    @property
    def daily_types(self):
        return [dailytype.CadenceSpeed(), dailytype.RotatingSpeed()]

    def spoilerchat_channel(self, daily_type):
        return self.daily(daily_type).spoilerchat_channel

    def leaderboard_channel(self, daily_type):
        return self.daily(daily_type).leaderboard_channel

    def is_spoilerchat_channel(self, channel):
        return channel == self._cadence_daily.spoilerchat_channel or channel == self._rotating_daily.spoilerchat_channel

    def get_type_for_spoilerchat(self, channel):
        if channel == self._cadence_daily.spoilerchat_channel:
            return dailytype.CalledType(dailytype.CadenceSpeed(), self._cadence_daily.today_number, explicit_char=True, for_previous=False)
        elif channel == self._rotating_daily.spoilerchat_channel:
            return dailytype.CalledType(dailytype.RotatingSpeed(), self._rotating_daily.today_number, explicit_char=True, for_previous=False)            

    @property
    def today_number(self):
        return self._cadence_daily.today_number

    def daily(self, daily_type):
        if daily_type == dailytype.CadenceSpeed():
            return self._cadence_daily
        elif daily_type == dailytype.RotatingSpeed():
            return self._rotating_daily
        else:
            return None

    # Do whatever UI things need to be done when a new daily happens
    @asyncio.coroutine
    def on_new_daily(self, daily):
        daily_type = daily.daily_type
        today_date = daily.today_date
        today_number = daily.today_number
        today_seed = daily.get_seed(today_number)
        character = daily_type.character(today_number)
        
        # Make the leaderboard message
        text = daily.leaderboard_text(today_number, display_seed=False)
        msg = yield from self.client.send_message(daily.leaderboard_channel, text)
        daily.register_message(today_number, msg.id)

        # Update yesterday's leaderboard with the seed
        asyncio.ensure_future(self.update_leaderboard(today_number - 1, daily_type, display_seed=True))

        # Announce the new daily in spoilerchat
        asyncio.ensure_future(self.client.send_message(daily.spoilerchat_channel, "The {0} {1} daily has begun!".format(today_date.strftime("%B %d"), character)))
                
        # PM users with the daily_alert preference
        auto_pref = userprefs.UserPrefs()
        if daily_type == dailytype.CadenceSpeed():
            auto_pref.daily_alert = userprefs.DailyAlerts['cadence']
        elif daily_type == dailytype.RotatingSpeed():
            auto_pref.daily_alert = userprefs.DailyAlerts['rotating']
            
        for member in self.necrobot.prefs.get_all_matching(auto_pref):
            if daily.has_submitted(today_number - 1, member.id) or not daily.has_registered(today_number - 1, member.id):
                daily.register(today_number, member.id)
                asyncio.ensure_future(self.client.send_message(member, "({0}) Today's {2} speedrun seed: {1}".format(today_date.strftime("%d %b"), today_seed, character)))
            else:
                asyncio.ensure_future(self.client.send_message(member, "You have not yet submitted for yesterday's {0} daily, so I am not yet sending you today's seed. " \
                                                                        "When you want today's seed, please call `.dailyseed` in the main channel or via PM. (Use `.dailyseed -override` " \
                                                                        "to get today's seed and forfeit your ability to submit for yesterday's daily.)".format(character)))                        

        # Hide dailyspoilerchat for those users with that preference
        hide_pref = userprefs.UserPrefs()
        hide_pref.hide_spoilerchat = True
        members_to_hide_for = self.necrobot.prefs.get_all_matching(hide_pref)
        for member in members_to_hide_for:
            read_permit = discord.Permissions.none()
            read_permit.read_messages = True
            yield from self.client.edit_channel_permissions(daily.spoilerchat_channel, member, deny=read_permit)

    # Update an existing leaderboard message for the given daily number
    @asyncio.coroutine
    def update_leaderboard(self, daily_number, daily_type, display_seed=False):
        daily = self.daily(daily_type)
        msg_id = daily.get_message_id(daily_number)

        #If no message, make one
        if not msg_id:
            text = daily.leaderboard_text(daily_number, display_seed)
            msg = yield from self.client.send_message(daily.leaderboard_channel, text)
            daily.register_message(daily_number, msg.id)
        else:
            msg_list = yield from self.client.logs_from(daily.leaderboard_channel, 10) #TODO: 10 is a "big enough" hack; make this more precise
            for msg in msg_list:
                if int(msg.id) == msg_id:
                    asyncio.ensure_future(self.client.edit_message(msg, daily.leaderboard_text(daily_number, display_seed)))

    # Called when a user updates their preferences with the given UserPrefs
    # Base method does nothing; override for functionality
    @asyncio.coroutine
    def on_update_prefs(self, prefs, member):
        for daily_type in [dailytype.CadenceSpeed(), dailytype.RotatingSpeed()]:
            daily = self.daily(daily_type)
            today_daily = daily.today_number
            if prefs.hide_spoilerchat == True and not daily.has_submitted(today_daily, member.id):
                read_permit = discord.Permissions.none()
                read_permit.read_messages = True
                yield from self.client.edit_channel_permissions(daily.spoilerchat_channel, member, deny=read_permit)  
            elif prefs.hide_spoilerchat == False:
                yield from self.client.delete_channel_permissions(daily.spoilerchat_channel, member)
