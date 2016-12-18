import calendar
import datetime
from .command import CommandType
from ..daily import dailytype


class DailyCommandType(CommandType):
    def __init__(self, bot_channel, *args):
        CommandType.__init__(self, bot_channel, *args)

    @property
    def _daily_manager(self):
        return self.necrobot.daily_manager

    @property
    def client(self):
        return self._daily_manager.necrobot.client

    async def _do_execute(self, command):
        today_number = self._daily_manager.today_number
        daily_type = dailytype.parse_out_type(command.args, today_number)

        if daily_type:
            await self._daily_do_execute(command, daily_type)
        else:
            await self.client.send_message(
                command.channel,
                "{0}: I couldn't figure out which daily you wanted to call a command for.".format(
                    command.author.mention))

    async def _daily_do_execute(self, command, called_type):
        pass


class DailyChar(DailyCommandType):
    def __init__(self, bot_channel):
        DailyCommandType.__init__(self, bot_channel, 'dailychar', 'dailywho')
        self.help_text = 'Get the character for the current rotating-character daily.'

    async def _daily_do_execute(self, command, daily_type):
        character = dailytype.character(dailytype.DailyType.rotating, self._daily_manager.today_number)
        await self.client.send_message(
            command.channel,
            'Today\'s character is {0}.'.format(character))


class DailyResubmit(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailyresubmit')
        self.help_text = 'Submit for the Cadence daily, overriding a previous submission. Use this to correct a ' \
                         'mistake in a daily submission. (Use the `rot` flag to resubmit for the rotating-character ' \
                         'daily.)'

    async def _daily_do_execute(self, command, daily_type):
        daily = self._daily_manager.daily(daily_type)

        last_submitted = daily.submitted_daily(command.author.id)
        character = dailytype.character(daily_type, last_submitted)

        if last_submitted == 0:
            await self.client.send_message(
                command.channel,
                "{0}: You've never submitted for a daily of this type.".format(command.author.mention))
        elif not daily.is_open(last_submitted):
            await self.client.send_message(
                command.channel,
                "{0}: The {1} {2} daily has closed.".format(
                    command.author.mention,
                    daily.daily_to_shortstr(last_submitted),
                    character))
        else:
            submission_string = daily.parse_submission(last_submitted, command.author, command.args)
            if submission_string:   # parse succeeded
                await self.client.send_message(
                    command.channel,
                    "Reubmitted for {0}, {2}: You {1}.".format(
                        daily.daily_to_shortstr(last_submitted),
                        submission_string,
                        character))

            else:                   # parse failed
                await self.client.send_message(
                    command.channel,
                    "{0}: I had trouble parsing your submission. Please use one of the forms: `{1} 12:34.56` "
                    "or `{1} death 4-4`.".format(command.author.mention, self.mention))


class DailyRules(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailyrules')
        self.help_text = 'Get the rules for the speedrun daily.'

    async def _daily_do_execute(self, command, daily_type):
        character = dailytype.character(daily_type, self._daily_manager.today_number)
        # noinspection PyUnresolvedReferences
        await self.client.send_message(
            command.channel,
            "Rules for the {0} speedrun daily:\n"
            "\N{BULLET} {0} seeded all zones; get the seed for the daily using `.dailyseed`.\n"
            "\N{BULLET} Run the seed blind. Make one attempt and submit the result (even if you die).\n"
            "\N{BULLET} No restriction on resolution, display settings, zoom, etc.\n"
            "\N{BULLET} Mods that disable leaderboard submission are not allowed (e.g. xml / music mods).".format(
                character))


class DailySchedule(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailyschedule')
        self.help_text = 'See the scheduled characters for the next few days.'

    async def _daily_do_execute(self, command, called_type):
        char_list_str = ''
        today_number = self._daily_manager.today_number
        today_char = dailytype.character(dailytype.DailyType.rotating, today_number)
        char_found = False
        for charname in dailytype.rotating_daily_chars:
            if charname == today_char:
                char_found = True
            if char_found:
                char_list_str += charname + ' -- '
        for charname in dailytype.rotating_daily_chars:
            if charname == today_char:
                break
            else:
                char_list_str += charname + ' -- '
        char_list_str = char_list_str[:-4]
        await self.client.send_message(
            command.channel,
            'Upcoming characters, starting today: {0}.'.format(char_list_str))


class DailySeed(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailyseed')
        self.help_text = 'Get the seed for today\'s Cadence daily. ' \
                         'Use the `-rot` flag to get the rotating-character daily seed.'

    async def _daily_do_execute(self, command, daily_type):
        daily = self._daily_manager.daily(daily_type)
        user_id = int(command.author.id)

        today = self._daily_manager.today_number
        today_date = daily.daily_to_date(today)

        character = dailytype.character(daily_type, today)

        if daily.has_submitted(today, user_id):
            await self.client.send_message(
                command.channel,
                "{0}: You have already submitted for today's {1} daily.".format(command.author.mention, character))
        else:
            daily.register(today, user_id)
            seed = daily.get_seed(today)
            await self.client.send_message(
                command.author,
                "({0}) {2} speedrun seed: {1}. This is a single-attempt {2} seeded all zones run. (See `.dailyrules` "
                "for complete rules.)".format(today_date.strftime("%d %b"), seed, character))


class DailyStatus(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailystatus')
        self.help_text = "Find out whether you've submitted to today's dailies."

    async def _daily_do_execute(self, command, daily_type):
        status = ''
        today_number = self._daily_manager.today_number

        for dtype in dailytype.DailyType:
            daily = self._daily_manager.daily(dtype)
            character = dailytype.character(dtype, today_number)
            old_char = dailytype.character(dtype, today_number - 1)
            last_registered = daily.registered_daily(command.author.id)
            days_since_registering = today_number - last_registered
            submitted = daily.has_submitted(last_registered, command.author.id)

            if days_since_registering == 1 and not submitted and daily.within_grace_period():
                status += "You have not gotten today's {1} seed. You may still submit for yesterday's {2} daily, " \
                          "which is open for another {0}. ".format(daily.daily_grace_timestr(), character, old_char)
            elif days_since_registering != 0:
                status += "You have not yet registered for the {0} daily: " \
                          "Use `.dailyseed` to get today's seed. ".format(character)
            elif submitted:
                status += "You have submitted to the {1} daily. " \
                          "The next daily opens in {0}. ".format(daily.next_daily_timestr(), character)
            else:
                status += "You have not yet submitted to the {1} daily: Use `.dailysubmit` to submit a result. " \
                          "Today's {1} daily is open for another {0}. ".format(daily.daily_close_timestr(), character)

        await self.client.send_message(command.channel, '{0}: {1}'.format(command.author.mention, status))


class DailySubmit(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailysubmit')
        self.help_text = "Submit a result for your most recent Cadence daily (use the `-rot` flag to submit for " \
                         "rotating-character dailies). Daily submissions close an hour after the next daily opens. " \
                         "If you complete the game during the daily, submit your time in the form [m]:ss.hh, e.g.: " \
                         "`.dailysubmit 12:34.56`. If you die during the daily, you may submit your run as " \
                         "`.dailysubmit death` or provide the level of death, e.g. `.dailysubmit death 4-4` for a " \
                         "death on dead ringer. This command can be called in the appropriate spoilerchat or via PM."

    async def _daily_do_execute(self, command, daily_type):
        daily = self._daily_manager.daily(daily_type)

        # Command sent via PM or in #dailyspoilerchat
        daily_number = daily.registered_daily(command.author.id)
        character = dailytype.character(daily_type, daily_number)

        if daily_number == 0:
            await self.client.send_message(
                command.channel,
                "{0}: Please get today's {1} daily seed before submitting (use `.dailyseed`).".format(
                    command.author.mention,
                    character))
        elif not daily.is_open(daily_number):
            await self.client.send_message(
                command.channel,
                "{0}: Too late to submit for the {1} {2} daily. Get today's seed with `.dailyseed`.".format(
                    command.author.mention,
                    daily.daily_to_shortstr(daily_number),
                    character))
        elif daily.has_submitted(daily_number, command.author.id):
            await self.client.send_message(
                command.channel,
                "{0}: You have already submitted for the {1} {2} daily. "
                "Use `.dailyresubmit` to edit your submission.".format(
                    command.author.mention,
                    daily.daily_to_shortstr(daily_number),
                    character))
        else:
            submission_string = daily.parse_submission(daily_number, command.author, command.args)
            if submission_string:       # parse succeeded
                await self.client.send_message(
                    command.channel,
                    "Submitted for {0}, {2}: You {1}.".format(
                        daily.daily_to_shortstr(daily_number),
                        submission_string,
                        character))

            else:                       # parse failed
                await self.client.send_message(
                    command.channel,
                    "{0}: I had trouble parsing your submission. "
                    "Please use one of the forms: `{1} 12:34.56` or `{1} death 4-4`.".format(
                        command.author.mention,
                        self.mention))


class DailyUnsubmit(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailyunsubmit')
        self.help_text = 'Retract your most recent Cadence daily submission; this only works while the daily is ' \
                         'still open. (Use the `rot` flag to unsubmit for the rotating-character daily.)'

    async def _daily_do_execute(self, command, daily_type):
        daily = self._daily_manager.daily(daily_type)
        daily_number = daily.submitted_daily(command.author.id)
        character = dailytype.character(daily_type, daily_number)

        if daily_number == 0:
            if daily_type == dailytype.DailyType.cadence:
                daily_string = 'a Cadence'
            elif daily_type == dailytype.DailyType.rotating:
                daily_string = 'a rotating'
            else:
                daily_string = '<error>'

            await self.client.send_message(
                command.channel,
                "{0}: You've never submitted for {1} daily.".format(command.author.mention, daily_string))

        elif not daily.is_open(daily_number):
            await self.client.send_message(
                command.channel,
                "{0}: The {1} {2} daily has closed.".format(
                    command.author.mention,
                    daily.daily_to_shortstr(daily_number),
                    character))

        else:
            daily.delete_from_daily(daily_number, command.author)
            await self.client.send_message(
                command.channel,
                "Deleted your daily submission for {0}, {1}.".format(
                    daily.daily_to_shortstr(daily_number),
                    character))
            await self._daily_manager.update_leaderboard(daily_number, daily_type)


class DailyWhen(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailywhen', 'dailyinfo')
        self.help_text = 'Get the date for the current Cadence daily, and the time until the next daily opens. Use ' \
                         'the `-rot` flag to get information (including character) for the rotating-character daily.' \
                         'Calling `.dailywhen coda` will tell you when the next Coda daily is (likewise for other ' \
                         'characters).'

    async def _daily_do_execute(self, command, daily_type):
        today_number = self._daily_manager.today_number
        for arg in command.args:
            charname = arg.lstrip('-').capitalize()
            if charname in dailytype.rotating_daily_chars:
                days_until = dailytype.days_until(charname, today_number)
                if days_until == 0:
                    await self.client.send_message(
                        command.channel,
                        'The {0} daily is today!'.format(charname))
                    return
                elif days_until == 1:
                    await self.client.send_message(
                        command.channel,
                        'The {0} daily is tomorrow!'.format(charname))
                    return
                elif days_until is not None:
                    date = datetime.datetime.utcnow().date() + datetime.timedelta(days=days_until)
                    await self.client.send_message(
                        command.channel,
                        'The {0} daily is in {1} days ({2}, {3}).'.format(
                            charname,
                            days_until,
                            calendar.day_name[date.weekday()], date.strftime("%B %d")))
                    return

        if daily_type == dailytype.DailyType.rotating:
            await self.client.send_message(
                command.channel,
                "Today's rotating character is {0}.".format(dailytype.character(daily_type, today_number)))


# For debugging/testing
class ForceRunNewDaily(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'forcerunnewdaily')
        self.secret_command = True

    async def _daily_do_execute(self, command, daily_type):
        if int(command.author.id) == int(self._daily_manager.necrobot.admin_id):
            for daily_type in dailytype.DailyType:
                await self._daily_manager.on_new_daily(self._daily_manager.daily(daily_type))


class ForceUpdateLeaderboard(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'forceupdateleaderboard')
        self.admin_only = True

    async def _daily_do_execute(self, command, daily_type):
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

        for daily_type in dailytype.DailyType:
            number = self._daily_manager.today_number - days_back
            show_seed = show_seed or days_back > 0
            await self._daily_manager.update_leaderboard(number, daily_type, show_seed)
