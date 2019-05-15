import calendar
import datetime

from necrobot.daily import dailytype
from necrobot.botbase.commandtype import CommandType
from necrobot.daily.dailymgr import DailyMgr
from necrobot.daily.daily import Daily
from necrobot.daily.dailytype import DailyType
from necrobot.user import userlib


class DailyCommandType(CommandType):
    def __init__(self, bot_channel, *args):
        CommandType.__init__(self, bot_channel, *args)

    async def _do_execute(self, cmd):
        daily = DailyMgr().daily(dailytype.parse_out_type(cmd.args))

        if daily is not None:
            await self._daily_do_execute(cmd, daily)
        else:
            await cmd.channel.send(
                "{0}: I couldn't figure out which daily you wanted to call a command for.".format(
                    cmd.author.mention
                )
            )

    async def _daily_do_execute(self, cmd, daily: Daily):
        pass


class DailyChar(DailyCommandType):
    def __init__(self, bot_channel):
        DailyCommandType.__init__(self, bot_channel, 'dailychar', 'dailywho')
        self.help_text = 'Get the character for the current rotating-character daily.'

    @property
    def short_help_text(self):
        return 'Rotating-daily character.'

    async def _daily_do_execute(self, cmd, _):
        rotating_daily = DailyMgr().daily(DailyType.ROTATING)
        character = dailytype.character(DailyType.ROTATING, rotating_daily.today_number)
        await cmd.channel.send(
            'Today\'s character is {0}.'.format(character)
        )


class DailyResubmit(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailyresubmit')
        self.help_text = 'Submit for the Cadence daily, overriding a previous submission. Use this to correct a ' \
                         'mistake in a daily submission. (Use the `rot` flag to resubmit for the rotating-character ' \
                         'daily.)'

    @property
    def short_help_text(self):
        return 'Resubmit for daily.'

    async def _daily_do_execute(self, cmd, daily):
        user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)
        last_submitted = await daily.submitted_daily(user.user_id)
        character = dailytype.character(daily.daily_type, last_submitted)

        if last_submitted == 0:
            await cmd.channel.send(
                "{0}: You've never submitted for a daily of this type.".format(cmd.author.mention))
        elif not daily.is_open(last_submitted):
            await cmd.channel.send(
                "{0}: The {1} {2} daily has closed.".format(
                    cmd.author.mention,
                    daily.daily_to_shortstr(last_submitted),
                    character))
        else:
            submission_string = await daily.parse_submission(
                daily_number=last_submitted, user_id=user.user_id, args=cmd.args
            )
            if submission_string:   # parse succeeded
                await daily.update_leaderboard(last_submitted)
                await cmd.channel.send(
                    "Reubmitted for {0}, {2}: You {1}.".format(
                        daily.daily_to_shortstr(last_submitted),
                        submission_string,
                        character))

            else:                   # parse failed
                await cmd.channel.send(
                    "{0}: I had trouble parsing your submission. Please use one of the forms: `{1} 12:34.56` "
                    "or `{1} death 4-4`.".format(cmd.author.mention, self.mention))


class DailyRules(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailyrules')
        self.help_text = 'Get the rules for the speedrun daily.'

    async def _daily_do_execute(self, cmd, daily):
        character = dailytype.character(daily.daily_type, daily.today_number)
        # noinspection PyUnresolvedReferences
        await self.client.send_message(
            cmd.channel,
            "Rules for the {0} speedrun daily:\n"
            "\N{BULLET} {0} seeded all zones; get the seed for the daily using `.dailyseed`.\n"
            "\N{BULLET} Run the seed blind. Make one attempt and submit the result (even if you die).\n"
            "\N{BULLET} No restriction on resolution, display settings, zoom, etc.\n"
            "\N{BULLET} Mods that disable leaderboard submission are not allowed (e.g. xml / music mods).".format(
                character))


class DailySeed(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailyseed')
        self.help_text = 'Get the seed for today\'s Cadence daily. ' \
                         'Use the `-rot` flag to get the rotating-character daily seed.'

    @property
    def short_help_text(self):
        return 'Get daily seed.'

    async def _daily_do_execute(self, cmd, daily):
        user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)

        today = daily.today_number
        today_date = daily.daily_to_date(today)

        character = dailytype.character(daily.daily_type, today)

        if await daily.has_submitted(today, user.user_id):
            await cmd.channel.send(
                "{0}: You have already submitted for today's {1} daily.".format(cmd.author.mention, character))
        else:
            await daily.register(today, user.user_id)
            seed = await daily.get_seed(today)
            await cmd.channel.send(
                "({0}) {2} speedrun seed: {1}. This is a single-attempt {2} seeded all zones run. (See `.dailyrules` "
                "for complete rules.)".format(today_date.strftime("%d %b"), seed, character))


class DailyStatus(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailystatus')
        self.help_text = "Find out whether you've submitted to today's dailies."

    @property
    def short_help_text(self):
        return "Your status for today's dailies."

    async def _daily_do_execute(self, cmd, _):
        user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)
        status = ''

        for dtype in DailyType:
            daily = DailyMgr().daily(dtype)
            today_number = daily.today_number
            character = dailytype.character(dtype, today_number)
            old_char = dailytype.character(dtype, today_number - 1)
            last_registered = await daily.registered_daily(user.user_id)
            days_since_registering = today_number - last_registered
            submitted = await daily.has_submitted(last_registered, user.user_id)

            if days_since_registering == 1 and not submitted and daily.within_grace_period:
                status += "You have not gotten today's {1} seed. You may still submit for yesterday's {2} daily, " \
                          "which is open for another {0}. ".format(daily.daily_grace_timestr, character, old_char)
            elif days_since_registering != 0:
                status += "You have not yet registered for the {0} daily: " \
                          "Use `.dailyseed` to get today's seed. ".format(character)
            elif submitted:
                status += "You have submitted to the {1} daily. " \
                          "The next daily opens in {0}. ".format(daily.next_daily_timestr, character)
            else:
                status += "You have not yet submitted to the {1} daily: Use `.dailysubmit` to submit a result. " \
                          "Today's {1} daily is open for another {0}. ".format(daily.daily_close_timestr, character)

        await cmd.channel.send('{0}: {1}'.format(cmd.author.mention, status))


class DailySubmit(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailysubmit')
        self.help_text = "Submit a result for your most recent Cadence daily (use the `-rot` flag to submit for " \
                         "rotating-character dailies). Daily submissions close an hour after the next daily opens. " \
                         "If you complete the game during the daily, submit your time in the form [m]:ss.hh, e.g.: " \
                         "`{0} 12:34.56`. If you die during the daily, you may submit your run as " \
                         "`{0} death` or provide the level of death, e.g. `{0} death 4-4` for a " \
                         "death on dead ringer.".format(self.mention)

    @property
    def short_help_text(self):
        return 'Submit daily result.'

    async def _daily_do_execute(self, cmd, daily):
        user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)

        daily_number = await daily.registered_daily(user.user_id)
        character = dailytype.character(daily.daily_type, daily_number)

        if daily_number == 0:
            await cmd.channel.send(
                "{0}: Please get today's {1} daily seed before submitting (use `.dailyseed`).".format(
                    cmd.author.mention,
                    character))
            return

        if not daily.is_open(daily_number):
            await cmd.channel.send(
                "{0}: Too late to submit for the {1} {2} daily. Get today's seed with `.dailyseed`.".format(
                    cmd.author.mention,
                    daily.daily_to_shortstr(daily_number),
                    character))
            return

        if await daily.has_submitted(daily_number, user.user_id):
            await cmd.channel.send(
                "{0}: You have already submitted for the {1} {2} daily. "
                "Use `.dailyresubmit` to edit your submission.".format(
                    cmd.author.mention,
                    daily.daily_to_shortstr(daily_number),
                    character))
            return

        submission_string = await daily.parse_submission(daily_number=daily_number, user_id=user.user_id, args=cmd.args)
        if not submission_string:
            await cmd.channel.send(
                "{0}: I had trouble parsing your submission. "
                "Please use one of the forms: `{1} 12:34.56` or `{1} death 4-4`.".format(
                    cmd.author.mention,
                    self.mention
                )
            )
            return

        await daily.update_leaderboard(daily_number)
        await cmd.channel.send(
            "Submitted for {0}, {2}: You {1}.".format(
                daily.daily_to_shortstr(daily_number),
                submission_string,
                character
            )
        )


class DailyUnsubmit(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailyunsubmit')
        self.help_text = 'Retract your most recent Cadence daily submission; this only works while the daily is ' \
                         'still open. (Use the `rot` flag to unsubmit for the rotating-character daily.)'

    @property
    def short_help_text(self):
        return 'Retract most recent submission.'

    async def _daily_do_execute(self, cmd, daily):
        user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)

        daily_number = await daily.submitted_daily(user.user_id)
        character = dailytype.character(daily.daily_type, daily_number)

        if daily_number == 0:
            await cmd.channel.send(
                "{0}: You've never submitted for {1} daily.".format(cmd.author.mention, daily.daily_type)
            )
            return

        if not daily.is_open(daily_number):
            await cmd.channel.send(
                "{0}: The {1} {2} daily has closed.".format(
                    cmd.author.mention,
                    daily.daily_to_shortstr(daily_number),
                    character
                )
            )
            return

        await daily.delete_from_daily(daily_number, user.user_id)
        await cmd.channel.send(
            "Deleted your daily submission for {0}, {1}.".format(
                daily.daily_to_shortstr(daily_number),
                character
            )
        )
        await daily.update_leaderboard(daily_number)


class DailyWhen(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'dailywhen', 'dailyschedule')
        self.help_text = 'Get upcoming daily characters. Use `.{0} charname` to find out when the next daily for ' \
                         'the given character is.'

    async def _daily_do_execute(self, cmd, daily):
        today_number = daily.today_number

        for arg in cmd.args:
            charname = arg.lstrip('-').capitalize()
            if charname in dailytype.rotating_daily_chars:
                days_until = dailytype.days_until(charname, today_number)
                if days_until == 0:
                    await cmd.channel.send(
                        'The {0} daily is today!'.format(charname)
                    )
                    return
                elif days_until == 1:
                    await cmd.channel.send(
                        'The {0} daily is tomorrow!'.format(charname)
                    )
                    return
                elif days_until is not None:
                    date = datetime.datetime.utcnow().date() + datetime.timedelta(days=days_until)
                    await cmd.channel.send(
                        'The {0} daily is in {1} days ({2}, {3}).'.format(
                            charname,
                            days_until,
                            calendar.day_name[date.weekday()], date.strftime("%B %d")
                        )
                    )
                    return

        # If here, there were no args, so get a schedule
        char_list_str = ''
        today_number = DailyMgr().daily(DailyType.ROTATING).today_number
        today_char = dailytype.character(DailyType.ROTATING, today_number)
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
        await cmd.channel.send(
            'Upcoming characters, starting today: {0}.'.format(char_list_str)
        )


# For debugging/testing
class ForceRunNewDaily(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'forcerunnewdaily')
        self.admin_only = True
        self.testing_command = True

    async def _daily_do_execute(self, cmd, daily):
        await daily.on_new_daily()


class ForceUpdateLeaderboard(DailyCommandType):
    def __init__(self, daily_module):
        DailyCommandType.__init__(self, daily_module, 'forceupdateleaderboard')
        self.admin_only = True
        self.testing_command = True

    async def _daily_do_execute(self, cmd, daily):
        days_back = 0
        show_seed = False
        for arg in cmd.args:
            if arg.lstrip('-').lower() == 'showseed':
                show_seed = True

            try:
                arg_as_int = int(arg)
                days_back = arg_as_int
            except ValueError:
                pass

        number = daily.today_number - days_back
        show_seed = show_seed or days_back > 0
        await daily.update_leaderboard(number, show_seed)
