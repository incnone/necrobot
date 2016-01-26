import asyncio
import command
import config
import daily

class DailyResubmit(command.CommandType):
    def __init__(self, daily_module):
        command.CommandType.__init__(self, 'dailyresubmit')
        self.help_text = 'Submit for the daily, overriding a previous submission. Use this to correct a mistake in a daily submission.'
        self._dm = daily_module       

    @asyncio.coroutine
    def _do_execute(self, command):

        client = self._dm.client
        manager = self._dm.manager
        
        # Command sent via PM or in #dailyspoilerchat
        if command.is_private or command.channel == self._dm._spoilerchat_channel:
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
                    asyncio.ensure_future(client.send_message(command.channel,
                        "Resubmitted for {0}: {1} {2}.".format(daily.daily_to_shortstr(daily_number), command.author.mention, submission_string)))
                    asyncio.ensure_future(manager.update_leaderboard(daily_number))
                else: # parse failed
                    asyncio.ensure_future(client.send_message(command.channel,
                        "{0}: I had trouble parsing your submission. Please use one of the forms: `.dailysubmit 12:34.56` or `.dailysubmit death 4-4`.".format(command.author.mention)))  

        # Command sent in main channel
        elif command.channel == self._dm.main_channel:
            
            asyncio.ensure_future(client.send_message(command.channel,
                "{0}: Please call `{1}` from {2} (this helps avoid spoilers in the main channel).".format(command.author.mention, self.mention, self._dm._spoilerchat_channel.mention)))      
            asyncio.ensure_future(client.delete_message(command.message))

class DailyRules(command.CommandType):
    def __init__(self, daily_module):
        command.CommandType.__init__(self, 'dailyrules')
        self.help_text = 'Get the rules for the speedrun daily.'
        self._dm = daily_module

    @asyncio.coroutine
    def _do_execute(self, command):
        if command.is_private or command.channel == self._dm.main_channel or command.channel == self._dm._spoilerchat_channel:
            client = self._dm._necrobot.client
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

    @asyncio.coroutine
    def _do_execute(self, command):
        if command.is_private or command.channel == self._dm.main_channel:
            client = self._dm.client
            manager = self._dm.manager
            user_id = command.author.id
            
            today = manager.today_number()
            today_date = daily.daily_to_date(today)
            if manager.has_submitted(today, user_id):
                asyncio.ensure_future(client.send_message(command.channel, "{0}: You have already submitted for today's daily.".format(command.author.mention)))
            elif manager.within_grace_period() and manager.has_registered(today - 1, user_id) and not manager.has_submitted(today - 1, user_id) and not (len(args) == 1 and args[0].lstrip('-') == 'override'):
                asyncio.ensure_future(client.send_message(member, "{0}: Warning: You have not yet " \
                    "submitted for yesterday's daily, which is open for another {1}. If you want to forfeit the " \
                    "ability to submit for yesterday's daily and get today's seed, call `.dailyseed -override`.".format(command.author.mention, manager.daily_grace_timestr())))                
            else:
                manager.register(today, user_id)
                seed = yield from manager.get_seed(today)
                asyncio.ensure_future(client.send_message(command.author, "({0}) Today's Cadence speedrun seed: {1}. " \
                    "This is a single-attempt Cadence seeded all zones run. (See `.dailyrules` for complete rules.)".format(today_date.strftime("%d %b"), seed)))                                                

class DailyStatus(command.CommandType):
    def __init__(self, daily_module):
        command.CommandType.__init__(self, 'dailystatus')
        self.help_text = 'Find out whether you\'ve submitted to today\'s daily.'
        self._dm = daily_module

    @asyncio.coroutine
    def _do_execute(self, command):
        if command.is_private or command.channel == self._dm.main_channel:
            client = self._dm.client
            status = ''        
            manager = self._dm.manager
            daily_number = manager.registered_daily(command.author.id)
            days_since_registering = manager.today_number() - daily_number
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
                submission_string = manager.parse_submission(daily_number, command.author, args)
                if submission_string: # parse succeeded
                    if command.is_private: # submitted through pm
                        asyncio.ensure_future(client.send_message(command.channel,
                            "Submitted for {0}: You {1}.".format(daily.daily_to_shortstr(daily_number), submission_string)))
                    #always post to spoilerchat
                    asyncio.ensure_future(client.send_message(manager._spoilerchat_channel,
                        "Submitted for {0}: {1} {2}.".format(daily.daily_to_shortstr(daily_number), command.author.mention, submission_string)))
                    asyncio.ensure_future(manager.update_leaderboard(daily_number))
                else: # parse failed
                    asyncio.ensure_future(client.send_message(command.channel,
                        "{0}: I had trouble parsing your submission. Please use one of the forms: `.dailysubmit 12:34.56` or `.dailysubmit death 4-4`.".format(command.author.mention)))

        # Command sent in main channel
        elif command.channel == self._dm.main_channel:
            
            asyncio.ensure_future(client.send_message(command.channel,
                "{0}: Please call `{1}` from {2} (this helps avoid spoilers in the main channel).".format(command.author.mention, self.mention, self._dm._spoilerchat_channel.mention)))      
            asyncio.ensure_future(client.delete_message(command.message))

class DailyUnsubmit(command.CommandType):
    def __init__(self, daily_module):
        command.CommandType.__init__(self, 'dailyunsubmit')
        self.help_text = 'Retract your most recent daily submission (only works while the daily is still open).'
        self._dm = daily_module

    @asyncio.coroutine
    def _do_execute(self, command):
        if command.is_private or command.channel == self._dm._spoilerchat_channel or command.channel == self._dm.main_channel:
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
                asyncio.ensure_future(manager.update_leaderboard(daily_number))        

class DailyWhen(command.CommandType):
    def __init__(self, daily_module):
        command.CommandType.__init__(self, 'dailywhen')
        self.help_text = 'Get the date for the current daily, and the time until the next daily opens.'
        self._dm = daily_module

    @asyncio.coroutine
    def _do_execute(self, command):
        if command.is_private or command.channel == self._dm._spoilerchat_channel or command.channel == self._dm.main_channel:
            asyncio.ensure_future(self._dm.client.send_message(command.channel, self._dm.manager.daily_time_info_str()))
            
class DailyModule(command.Module):
    def __init__(self, necrobot, db_connection):
        self._necrobot = necrobot
        self._db_conn = db_connection
        self._manager = daily.DailyManager(necrobot.client, db_connection, necrobot._pref_manager) #TODO
        self._spoilerchat_channel = necrobot.find_channel(config.DAILY_SPOILERCHAT_CHANNEL_NAME)
        self._leaderboard_channel = necrobot.find_channel(config.DAILY_LEADERBOARDS_CHANNEL_NAME)
        self._command_types = [DailyRules(self), DailySeed(self), DailyWhen(self)]

    @property
    def infostr(self):
        return 'Speedrun daily.'

    @property
    def client(self):
        return self._necrobot.client

    @property
    def main_channel(self):
        return self._necrobot.main_channel

    @property
    def manager(self):
        return self._manager

    @asyncio.coroutine
    def execute(self, command):
        for cmd_type in self._command_types:
            yield from cmd_type.execute(command)
        
