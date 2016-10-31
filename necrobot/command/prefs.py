from necrobot.prefs.userprefs import UserPrefs
from .command import CommandType


class DailyAlert(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'dailyalert')
        self.help_text = "Set daily alerts on or off for your account. " \
                         "Use `{0} on` or `{0} off`.".format(self.mention)

    async def _do_execute(self, command):
        if len(command.args) != 1 or command.args[0].lower() not in ['on', 'off']:
            await self.necrobot.client.send_message(
                command.channel,
                "Couldn't parse command. Call `{0} on` or `{0} off`.".format(self.mention))
            return

        user_prefs = UserPrefs()
        if command.args[0] == 'on':
            user_prefs.daily_alert = True
        else:
            user_prefs.daily_alert = False

        self.necrobot.prefs_manager.set_prefs(user_prefs, command.author)


class RaceAlert(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'racealert')
        self.help_text = "Set race alerts on or off for your account. " \
                         "Use `{0} on` or `{0} off`.".format(self.mention)

    async def _do_execute(self, command):
        if len(command.args) != 1 or command.args[0].lower() not in ['on', 'off']:
            await self.necrobot.client.send_message(
                command.channel,
                "Couldn't parse command. Call `{0} on` or `{0} off`.".format(self.mention))
            return

        user_prefs = UserPrefs()
        if command.args[0] == 'on':
            user_prefs.race_alert = True
        else:
            user_prefs.race_alert = False

        self.necrobot.prefs_manager.set_prefs(user_prefs, command.author)


class ViewPrefs(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'viewprefs', 'getprefs')
        self.help_text = "See your current user preferences."

    async def _do_execute(self, command):
        prefs = self.necrobot.prefs_manager.get_prefs(command.author)
        prefs_string = ''
        for pref_str in prefs.pref_strings:
            prefs_string += ' ' + pref_str
        await self.necrobot.client.send_message(
            command.author,
            'Your current user preferences: {}'.format(prefs_string))
