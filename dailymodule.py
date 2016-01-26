import command
import config
import daily

class DailyResubmit(command.CommandType):
    def __init__(self, daily_module):
        command.CommandType.__init__(self, 'dailyresubmit')
        self.help_text = 'Submit for the daily, overriding a previous submission. Use this to correct a mistake in a daily submission.'
        self._dm = daily_module

    def _do_execute(command):

        client = self._dm._necrobot.client
        
        # Command sent via PM or in #dailyspoilerchat
        if command.channel.is_private or command.channel == self._dm._spoilerchat_channel:
            daily_number = self._dm.submitted_daily(command.author.id)
            if daily_number == 0:
                asyncio.ensure_future(client.send_message(command.channel,
                    "{0}: You've never submitted for a daily.".format(command.author.mention)))
            elif not self._dm.is_open(daily_number):
                asyncio.ensure_future(client.send_message(command.channel,
                    "{0}: The {1} daily has closed.".format(command.author.mention, daily.daily_to_shortstr(daily_number))))
            else:
                submission_string = self._dm.parse_submission(daily_number, command.author, args, overwrite=True)
                if submission_string: # parse succeeded
                    asyncio.ensure_future(self._client.send_message(message.channel,
                        "Resubmitted for {0}: {1} {2}.".format(daily.daily_to_shortstr(daily_number), message.author.mention, submission_string)))
                    asyncio.ensure_future(dm.update_leaderboard(daily_number))
                else: # parse failed
                    asyncio.ensure_future(self._client.send_message(message.channel,
                        "{0}: I had trouble parsing your submission. Please use one of the forms: `.dailysubmit 12:34.56` or `.dailysubmit death 4-4`.".format(message.author.mention)))  

        # Command sent in main channel
        elif command.channel == self._dm._necrobot.main_channel:
            
            asyncio.ensure_future(self._dm._necrobot.client.send_message(message.channel,
                "{0}: Please call `{1}` from {2} (this helps avoid spoilers in the main channel).".format(command.author.mention, self.mention, self._dm._spoilerchat_channel.mention)))      
            asyncio.ensure_future(self._dm._necrobot.client.delete_message(message))


class DailyModule(command.Module):
    def __init__(self, necrobot, db_connection):
        self._necrobot = necrobot
        self._db_conn = db_connection
        self._spoilerchat_channel = necrobot.find_channel(config.DAILY_SPOILERCHAT_CHANNEL_NAME)
        self._leaderboard_channel = necrobot.find_channel(config.DAILY_LEADERBOARDS_CHANNEL_NAME)
        self._command_types = [DailyResubmit()]

    @property
    def infostr(self):
        return 'Speedrun daily.'

    def execute(self, command):
        for cmd_type in self._command_types:
            cmd_type.execute(command)
        
