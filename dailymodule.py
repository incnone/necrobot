import asyncio
import discord

import command
import config
import daily
import userprefs

class DailyResubmit(command.CommandType):
    def __init__(self, daily_module):
        command.CommandType.__init__(self, 'dailyresubmit')
        self.help_text = 'Submit for the daily, overriding a previous submission. Use this to correct a mistake in a daily submission.'
        self._dm = daily_module       

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._dm.spoilerchat_channel or channel == self._dm.main_channel

    @asyncio.coroutine
    def _do_execute(self, command):

        client = self._dm.client
        manager = self._dm.manager
        
        # Command sent via PM or in #dailyspoilerchat
        if command.is_private or command.channel == self._dm.spoilerchat_channel:
            daily_number = manager.submitted_daily(command.author.id)
            if daily_number == 0:
                asyncio.ensure_future(client.send_message(command.channel,
                    "{0}: You've never submitted for a daily.".format(command.author.mention)))
            elif not manager.is_open(daily_number):
                asyncio.ensure_future(client.send_message(command.channel,
                    "{0}: The {1} daily has closed.".format(command.author.mention, daily.daily_to_shortstr(daily_number))))
            else:
                submission_string = manager.parse_submission(daily_number, command.author, command.args, overwrite=True)
                if submission_string: # parse succeeded
                    # Respond in PM if submission is in PM
                    if command.is_private:
                        asyncio.ensure_future(client.send_message(command.channel,
                            "Reubmitted for {0}: You {1}.".format(daily.daily_to_shortstr(daily_number), submission_string)))

                    # Post to spoilerchat (regardless of where submission was)
                    asyncio.ensure_future(client.send_message(self._dm.spoilerchat_channel,
                        "Resubmitted for {0}: {1} {2}.".format(daily.daily_to_shortstr(daily_number), command.author.mention, submission_string)))
                    asyncio.ensure_future(self._dm.update_leaderboard(daily_number))

                else: # parse failed
                    asyncio.ensure_future(client.send_message(command.channel,
                        "{0}: I had trouble parsing your submission. Please use one of the forms: `.dailysubmit 12:34.56` or `.dailysubmit death 4-4`.".format(command.author.mention)))  

        # Command sent in main channel
        elif command.channel == self._dm.main_channel:
            
            asyncio.ensure_future(client.send_message(command.channel,
                "{0}: Please call `{1}` from {2} (this helps avoid spoilers in the main channel).".format(command.author.mention, self.mention, self._dm.spoilerchat_channel.mention)))      
            asyncio.ensure_future(client.delete_message(command.message))

class DailyRules(command.CommandType):
    def __init__(self, daily_module):
        command.CommandType.__init__(self, 'dailyrules')
        self.help_text = 'Get the rules for the speedrun daily.'
        self._dm = daily_module

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._dm.spoilerchat_channel or channel == self._dm.main_channel

    @asyncio.coroutine
    def _do_execute(self, command):
        client = self._dm.client
        asyncio.ensure_future(client.send_message(command.channel, "Rules for the speedrun daily:\n" \
            "\N{BULLET} Cadence seeded all zones; get the seed for the daily using `.dailyseed`.\n" \
            "\N{BULLET} Run the seed blind. Make one attempt and submit the result (even if you die).\n" \
            "\N{BULLET} No restriction on resolution, display settings, zoom, etc.\n" \
            "\N{BULLET} Mods that disable leaderboard submission are not allowed (e.g. xml / music mods).")) 

class DailySeed(command.CommandType):
    def __init__(self, daily_module):
        command.CommandType.__init__(self, 'dailyseed')
        self.help_text = 'Get the seed for today\'s daily. (Will be sent via PM.)'
        self._dm = daily_module

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._dm.main_channel

    @asyncio.coroutine
    def _do_execute(self, command):
        client = self._dm.client
        manager = self._dm.manager
        user_id = command.author.id
        
        today = manager.today_number
        today_date = daily.daily_to_date(today)
        if manager.has_submitted(today, user_id):
            asyncio.ensure_future(client.send_message(command.channel, "{0}: You have already submitted for today's daily.".format(command.author.mention)))
        elif manager.within_grace_period() and manager.has_registered(today - 1, user_id) and not manager.has_submitted(today - 1, user_id) and not (len(command.args) == 1 and command.args[0].lstrip('-') == 'override'):
            asyncio.ensure_future(client.send_message(member, "{0}: Warning: You have not yet " \
                "submitted for yesterday's daily, which is open for another {1}. If you want to forfeit the " \
                "ability to submit for yesterday's daily and get today's seed, call `.dailyseed -override`.".format(command.author.mention, manager.daily_grace_timestr())))                
        else:
            manager.register(today, user_id)
            seed = manager.get_seed(today)
            asyncio.ensure_future(client.send_message(command.author, "({0}) Today's Cadence speedrun seed: {1}. " \
                "This is a single-attempt Cadence seeded all zones run. (See `.dailyrules` for complete rules.)".format(today_date.strftime("%d %b"), seed)))                                                

class DailyStatus(command.CommandType):
    def __init__(self, daily_module):
        command.CommandType.__init__(self, 'dailystatus')
        self.help_text = 'Find out whether you\'ve submitted to today\'s daily.'
        self._dm = daily_module

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._dm.main_channel

    @asyncio.coroutine
    def _do_execute(self, command):
        client = self._dm.client
        status = ''        
        manager = self._dm.manager
        daily_number = manager.registered_daily(command.author.id)
        days_since_registering = manager.today_number - daily_number
        submitted = manager.has_submitted(daily_number, command.author.id)

        if days_since_registering == 1 and not submitted and manager.within_grace_period():
            status = "You have not gotten today's seed. You may still submit for yesterday's daily, which is open for another {0}.".format(manager.daily_grace_timestr())
        elif days_since_registering != 0:
            status = "You have not yet registered: Use `.dailyseed` to get today's seed."
        elif submitted:
            status = "You have submitted to the daily. The next daily opens in {0}.".format(manager.next_daily_timestr())
        else:
            status = "You have not yet submitted to the daily: Use `.dailysubmit` to submit a result. Today's daily is open for another {0}.".format(manager.daily_close_timestr())

        asyncio.ensure_future(client.send_message(command.channel, '{0}: {1}'.format(command.author.mention, status)))        

class DailySubmit(command.CommandType):
    def __init__(self, daily_module):
        command.CommandType.__init__(self, 'dailysubmit')
        self.help_text = "Submit a result for your most recent daily. Daily submissions close an hour after the next " \
                    "daily opens. If you complete the game during the daily, submit your time in the form [m]:ss.hh, e.g.: " \
                    "`.dailysubmit 12:34.56`. If you die during the daily, you may submit your run as `.dailysubmit death` " \
                    "or provide the level of death, e.g. `.dailysubmit death 4-4` for a death on dead ringer. This command can " \
                    "be called in {} or via PM.".format(daily_module._spoilerchat_channel.mention)
        self._dm = daily_module

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._dm.main_channel or channel == self._dm.spoilerchat_channel

    @asyncio.coroutine
    def _do_execute(self, command):
        client = self._dm.client

        # Command sent via PM or in #dailyspoilerchat
        if command.is_private or command.channel == self._dm.spoilerchat_channel:

            manager = self._dm.manager     
            daily_number = manager.registered_daily(command.author.id)

            if daily_number == 0:
                asyncio.ensure_future(client.send_message(command.channel,
                    "{0}: Please get today's daily seed before submitting (use `.dailyseed`).".format(command.author.mention, daily.daily_to_shortstr(daily_number))))
            elif not manager.is_open(daily_number):
                asyncio.ensure_future(client.send_message(command.channel,
                    "{0}: Too late to submit for the {1} daily. Get today's seed with `.dailyseed`.".format(command.author.mention, daily.daily_to_shortstr(daily_number))))
            elif manager.has_submitted(daily_number, command.author.id):
                asyncio.ensure_future(client.send_message(command.channel,
                    "{0}: You have already submitted for the {1} daily.".format(command.author.mention, daily.daily_to_shortstr(daily_number))))
            else:
                submission_string = manager.parse_submission(daily_number, command.author, command.args)
                if submission_string: # parse succeeded

                    # Respond in PM if submission is in PM
                    if command.is_private:
                        asyncio.ensure_future(client.send_message(command.channel,
                            "Submitted for {0}: You {1}.".format(daily.daily_to_shortstr(daily_number), submission_string)))

                    # Post to spoilerchat (regardless of where submission was)
                    asyncio.ensure_future(client.send_message(self._dm.spoilerchat_channel,
                        "Submitted for {0}: {1} {2}.".format(daily.daily_to_shortstr(daily_number), command.author.mention, submission_string)))
                    asyncio.ensure_future(self._dm.update_leaderboard(daily_number))

                    # If submitting for today, make spoilerchat visible
                    if daily_number == self._dm.manager.today_number:
                        read_permit = discord.Permissions.none()
                        read_permit.read_messages = True
                        yield from client.edit_channel_permissions(self._dm.spoilerchat_channel, self._dm.necrobot.get_as_member(command.author), allow=read_permit)
                    
                else: # parse failed
                    asyncio.ensure_future(client.send_message(command.channel,
                        "{0}: I had trouble parsing your submission. Please use one of the forms: `.dailysubmit 12:34.56` or `.dailysubmit death 4-4`.".format(command.author.mention)))

        # Command sent in main channel
        elif command.channel == self._dm.main_channel:
            asyncio.ensure_future(client.send_message(command.channel,
                "{0}: Please call `{1}` from {2}, or via PM (this helps avoid spoilers in the main channel).".format(command.author.mention, self.mention, self._dm.spoilerchat_channel.mention)))      
            asyncio.ensure_future(client.delete_message(command.message))

class DailyUnsubmit(command.CommandType):
    def __init__(self, daily_module):
        command.CommandType.__init__(self, 'dailyunsubmit')
        self.help_text = 'Retract your most recent daily submission (only works while the daily is still open).'
        self._dm = daily_module

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._dm.main_channel or channel == self._dm.spoilerchat_channel

    @asyncio.coroutine
    def _do_execute(self, command):
        client = self._dm.client
        manager = self._dm.manager
        daily_number = manager.submitted_daily(command.author.id)

        if daily_number == 0:
            asyncio.ensure_future(client.send_message(command.channel,
                "{0}: You've never submitted for a daily.".format(command.author.mention)))
        elif not manager.is_open(daily_number):
            asyncio.ensure_future(client.send_message(command.channel,
                "{0}: The {1} daily has closed.".format(command.author.mention, daily.daily_to_shortstr(daily_number))))
        else:
            manager.delete_from_daily(daily_number, command.author)
            asyncio.ensure_future(client.send_message(command.channel,
                "Deleted {1}'s daily submission for {0}.".format(daily.daily_to_shortstr(daily_number), command.author.mention)))
            asyncio.ensure_future(self._dm.update_leaderboard(daily_number))        

class DailyWhen(command.CommandType):
    def __init__(self, daily_module):
        command.CommandType.__init__(self, 'dailywhen')
        self.help_text = 'Get the date for the current daily, and the time until the next daily opens.'
        self._dm = daily_module

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._dm.main_channel or channel == self._dm.spoilerchat_channel

    @asyncio.coroutine
    def _do_execute(self, command):
        asyncio.ensure_future(self._dm.client.send_message(command.channel, self._dm.manager.daily_time_info_str()))

#For debugging/testing
class ForceRunNewDaily(command.CommandType): 
    def __init__(self, daily_module):
        command.CommandType.__init__(self, 'forcerunnewdaily')
        self.suppress_help = True
        self._dm = daily_module

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._dm.main_channel

    @asyncio.coroutine
    def _do_execute(self, command):
        if command.author.id == self._dm.necrobot._admin_id:
            yield from self._dm.on_new_daily()

class DailyModule(command.Module):
    def __init__(self, necrobot, db_connection):
        command.Module.__init__(self, necrobot)
        self._manager = daily.DailyManager(self, db_connection)
        self._spoilerchat_channel = necrobot.find_channel(config.DAILY_SPOILERCHAT_CHANNEL_NAME)
        self._leaderboard_channel = necrobot.find_channel(config.DAILY_LEADERBOARDS_CHANNEL_NAME)
        self.command_types = [command.DefaultHelp(self),
                              DailyResubmit(self),
                              DailyRules(self),
                              DailySeed(self),
                              DailyStatus(self),
                              DailySubmit(self),
                              DailyUnsubmit(self),
                              DailyWhen(self),
                              ForceRunNewDaily(self)]

    @property
    def infostr(self):
        return 'Speedrun daily'

    @property
    def main_channel(self):
        return self.necrobot.main_channel

    @property
    def spoilerchat_channel(self):
        return self._spoilerchat_channel

    @property
    def leaderboard_channel(self):
        return self._leaderboard_channel

    @property
    def manager(self):
        return self._manager

    # Do whatever UI things need to be done when a new daily happens
    @asyncio.coroutine
    def on_new_daily(self):
        today_date = self.manager.today_date
        today_number = self.manager.today_number
        today_seed = self.manager.get_seed(today_number)
        
        # Make the leaderboard message
        text = self.manager.leaderboard_text(today_number)
        msg = yield from self.client.send_message(self._leaderboard_channel, text)
        self.manager.register_message(today_number, msg.id)

        # Update yesterday's leaderboard with the seed
        asyncio.ensure_future(self.update_leaderboard(today_number - 1, True))

        # Announce the new daily in spoilerchat
        asyncio.ensure_future(self.client.send_message(self._spoilerchat_channel, "The {} daily has begun!".format(today_date.strftime("%B %d"))))
                
        # PM users with the daily_alert preference
        auto_pref = userprefs.UserPrefs()
        auto_pref.daily_alert = True
        for member in self.necrobot.prefs.get_all_matching(auto_pref):
            if self.manager.has_submitted(today_number - 1, member.id) or not self.manager.has_registered(today_number - 1, member.id):
                self.manager.register(today_number, member.id)
                asyncio.ensure_future(self.client.send_message(member, "({0}) Today's Cadence speedrun seed: {1}".format(today_date.strftime("%d %b"), today_seed)))
            else:
                asyncio.ensure_future(self.client.send_message(member, "You have not yet submitted for yesterday's daily, so I am not yet sending you today's seed. " \
                                                                        "When you want today's seed, please call `.dailyseed` in the main channel or via PM."))                        

        # Hide dailyspoilerchat for those users with that preference
        hide_pref = userprefs.UserPrefs()
        hide_pref.hide_spoilerchat = True
        members_to_hide_for = self.necrobot.prefs.get_all_matching(hide_pref)
        for member in members_to_hide_for:
            read_permit = discord.Permissions.none()
            read_permit.read_messages = True
            yield from self.client.edit_channel_permissions(self._spoilerchat_channel, member, deny=read_permit)

    # Update an existing leaderboard message for the given daily number
    @asyncio.coroutine
    def update_leaderboard(self, daily_number, display_seed=False):
        msg_id = self.manager.get_message_id(daily_number)
        if msg_id:
            msg_list = yield from self.client.logs_from(self._leaderboard_channel, 10) #TODO: 10 is a "big enough" hack; make this more precise
            for msg in msg_list:
                if int(msg.id) == msg_id:
                    asyncio.ensure_future(self.client.edit_message(msg, self.manager.leaderboard_text(daily_number, display_seed)))

    # Called when a user updates their preferences with the given UserPrefs
    # Base method does nothing; override for functionality
    @asyncio.coroutine
    def on_update_prefs(self, prefs, member):
        today_daily = self.manager.today_number
        if prefs.hide_spoilerchat == True and not self.manager.has_submitted(today_daily, member.id):
            read_permit = discord.Permissions.none()
            read_permit.read_messages = True
            yield from self.client.edit_channel_permissions(self._spoilerchat_channel, member, deny=read_permit)  
        elif prefs.hide_spoilerchat == False:
            read_permit = discord.Permissions.none()
            read_permit.read_messages = True
            yield from self.client.edit_channel_permissions(self._spoilerchat_channel, member, allow=read_permit)  
        
