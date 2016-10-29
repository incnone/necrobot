import asyncio

import command
from command import clparse

DailyAlerts = {'none':0, 'cadence':1, 'all':2, 'rotating':3}
RaceAlerts = {'none':0, 'some':1, 'all':2}

class UserPrefs(object):
    def get_default():
        prefs = UserPrefs()
        prefs.hide_spoilerchat = False
        prefs.daily_alert = DailyAlerts['none']
        prefs.race_alert = RaceAlerts['none']
        return prefs

    def __init__(self):
        self.hide_spoilerchat = None
        self.daily_alert = None
        self.race_alert = None

    def modify_with(self, user_prefs):
        if user_prefs.hide_spoilerchat != None:
            self.hide_spoilerchat = user_prefs.hide_spoilerchat
        if user_prefs.daily_alert != None:
            self.daily_alert = user_prefs.daily_alert
        if user_prefs.race_alert != None:
            self.race_alert = user_prefs.race_alert

    @property
    def contains_info(self):
        return self.hide_spoilerchat != None or self.daily_alert != None or self.race_alert != None

    # A list of strings describing preferences set by this object
    @property
    def pref_strings(self):
        pref_str = []
        if self.hide_spoilerchat == False:
            pref_str.append('Show daily spoiler chat at all times.')
        elif self.hide_spoilerchat == True:
            pref_str.append('Hide daily spoiler chat until after submission.')

        if self.daily_alert == DailyAlerts['none']:
            pref_str.append('No daily alerts.')
        elif self.daily_alert == DailyAlerts['cadence']:
            pref_str.append('Get the seed when the new Cadence daily opens.')
        elif self.daily_alert == DailyAlerts['all']:
            pref_str.append('Get both seeds (via PM) when the new dailies open.')
        elif self.daily_alert == DailyAlerts['rotating']:
            pref_str.append('Get the seed when the new rotating-character daily opens.')

        if self.race_alert == RaceAlerts['none']:
            pref_str.append('No race alerts.')
        elif self.race_alert == RaceAlerts['some']:
            pref_str.append('Alert (via PM) when a new race (not a rematch) begins.')
        elif self.race_alert == RaceAlerts['all']:
            pref_str.append('Alert (via PM) when any race begins (includes rematches).')

        return pref_str

def _parse_show_spoilerchat(args, user_prefs):
    command_list = ['spoilerchat']
    if len(args) >= 2 and args[0] in command_list:
        if args[1] == 'hide':
            user_prefs.hide_spoilerchat = True
        elif args[1] == 'show':
            user_prefs.hide_spoilerchat = False

def _parse_daily_alert(args, user_prefs):
    command_list = ['dailyalert']
    if len(args) >= 2 and args[0] in command_list and args[1] in DailyAlerts:
        user_prefs.daily_alert = DailyAlerts[args[1]]

def _parse_race_alert(args, user_prefs):
    command_list = ['racealert']
    if len(args) >= 2 and args[0] in command_list and args[1] in RaceAlerts:
        user_prefs.race_alert = RaceAlerts[args[1]]

def parse_args(args):
    #user_prefs is a list of preferences we should change
    user_prefs = UserPrefs()

    while args:
        next_cmd_args = clparse.pop_command(args)
        if not next_cmd_args:
            next_cmd_args.append(args[0])
            args.pop(0)

        #Parse each possible command
        _parse_show_spoilerchat(next_cmd_args, user_prefs)
        _parse_daily_alert(next_cmd_args, user_prefs)
        _parse_race_alert(next_cmd_args, user_prefs)
    #end while

    return user_prefs

class SetPrefs(command.CommandType):
    def __init__(self, prefs_module):
        command.CommandType.__init__(self, 'setprefs')
        self.help_text = "Set user preferences. Allowable flags:\n" \
                    "`-spoilerchat [show|hide]` : `show` makes spoilerchat visible at all times; `hide` hides it until you've submitted for the daily.\n" \
                    "`-dailyalert [none|all|cadence|rotating]` : sends the daily seed via PM when a new daily opens. `all` does this for both dailies; `cadence` " \
                    "or `rotating` restricts to the appropriate daily.\n" \
                    "`-racealert [none|some|all]` : `none` gives no race alerts; `some` sends a PM when a new race is created (but not a rematch); `all` sends a " \
                    "PM for every race created (including rematches)."
        self._pm = prefs_module

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._pm.necrobot.main_channel

    @asyncio.coroutine
    def _do_execute(self, command):
        prefs = parse_args(command.args)
        if prefs.contains_info:
            asyncio.ensure_future(self._pm.set_prefs(prefs, command.author))
            confirm_msg = 'Set the following preferences for {}:'.format(command.author.mention)
            for pref_str in prefs.pref_strings:
                confirm_msg += ' ' + pref_str
            asyncio.ensure_future(self._pm.client.send_message(command.channel, confirm_msg))
        else:
            asyncio.ensure_future(self._pm.client.send_message(command.channel, '{0}: Failure parsing arguments; did not set any user preferences.'.format(command.author.mention)))

class ViewPrefs(command.CommandType):
    def __init__(self, prefs_module):
        command.CommandType.__init__(self, 'viewprefs', 'getprefs')
        self.help_text = "See your current user preferences."
        self._pm = prefs_module

    def recognized_channel(self, channel):
        return channel.is_private or channel == self._pm.necrobot.main_channel

    @asyncio.coroutine
    def _do_execute(self, command):
        prefs = self._pm.get_prefs(command.author)
        prefs_string = ''
        for pref_str in prefs.pref_strings:
            prefs_string += ' ' + pref_str
        yield from self._pm.client.send_message(command.author, 'Your current user preferences: {}'.format(prefs_string))

class PrefsModule(command.Module):
    def __init__(self, necrobot, necrodb):
        command.Module.__init__(self, necrobot)
        self.necrodb = necrodb
        self.command_types = [command.DefaultHelp(self),
                              SetPrefs(self),
                              ViewPrefs(self)]

    @property
    def infostr(self):
        return 'User preferences'

    @asyncio.coroutine
    def set_prefs(self, user_prefs, user):
        prefs = self.get_prefs(user)
        prefs.modify_with(user_prefs)

        params = (user.id, prefs.hide_spoilerchat, prefs.daily_alert, prefs.race_alert,)
        self.necrodb.set_prefs(params)

        for module in self.necrobot.modules:
            yield from module.on_update_prefs(user_prefs, self.necrobot.get_as_member(user))

    def get_prefs(self, user):
        user_prefs = UserPrefs.get_default()
        params = (user.id,)
        for row in self.necrodb.get_prefs(params):
            user_prefs.hide_spoilerchat = row[1]
            user_prefs.daily_alert = row[2]
            user_prefs.race_alert = row[3]
        return user_prefs

    #get all user id's matching the given user prefs
    def get_all_matching(self, user_prefs):
        users_matching_spoilerchat = []
        users_matching_dailyalert = []
        users_matching_racealert = []
        lists_to_use = []

        if user_prefs.hide_spoilerchat != None:
            lists_to_use.append(users_matching_spoilerchat)
            params = (user_prefs.hide_spoilerchat,)
            for row in self.necrodb.get_all_matching_prefs("hidespoilerchat", params):
                userid = row[0]
                for member in self.necrobot.server.members:
                    if int(member.id) == int(userid):
                        users_matching_spoilerchat.append(member)

        if user_prefs.daily_alert != None:
            lists_to_use.append(users_matching_dailyalert)
            params = (user_prefs.daily_alert,)
            if user_prefs.daily_alert != DailyAlerts['none'] and user_prefs.daily_alert != DailyAlerts['all']:
                params += (DailyAlerts['all'],)
            else:
                params += (user_prefs.daily_alert,)

            for row in self.necrodb.get_all_matching_prefs("dailyalert", params):
                userid = row[0]
                for member in self.necrobot.server.members:
                    if int(member.id) == int(userid):
                        users_matching_dailyalert.append(member)

        if user_prefs.race_alert != None:
            lists_to_use.append(users_matching_racealert)
            params = (user_prefs.race_alert,)
            if user_prefs.race_alert == RaceAlerts['some']:
                params += (RaceAlerts['all'],)
            else:
                params += (user_prefs.race_alert,)

            for row in self.necrodb.get_all_matching_prefs("racealert", params):
                userid = row[0]
                for member in self.necrobot.server.members:
                    if int(member.id) == int(userid):
                        users_matching_racealert.append(member)

        users_matching = []
        if lists_to_use:
            for member in lists_to_use[0]:
                in_intersection = True
                for l in lists_to_use:
                    if not member in l:
                        in_interesection = False
                if in_intersection:
                    users_matching.append(member)
        return users_matching
