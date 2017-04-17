import datetime
import pytz
from necrobot.botbase.command import CommandType
from necrobot.user.necrouser import NecroUser
from necrobot.util.parse import dateparse
from necrobot.util import timestr
from necrobot.util.parse.exception import ParseException


# Matchroom commands
class Confirm(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'confirm')
        self.help_text = 'Confirm that you agree to the suggested time for this match.'

    async def _do_execute(self, cmd):
        pass


class Postpone(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'postpone')
        self.help_text = 'Postpones the match. An admin can resume with `.f-begin`.'

    async def _do_execute(self, cmd):
        pass


class Suggest(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'suggest')
        self.help_text = 'Suggest a time to schedule a match (your local time). Examples:\n' \
                         '   `.suggest Feb 18 17:30`' \
                         '   `.suggest Thursday 8p`' \
                         '   `.suggest today 9:15pm`' \
                         '   `.suggest now'

    async def _do_execute(self, cmd):
        # Get the match
        match = self.bot_channel.match
        if not match:
            await self.necrobot.client.send_message(
                cmd.channel,
                'Error: This match wasn\'t found in the database. Please contact CoNDOR Staff.')
            return

        # Check for match already being confirmed
        if match.is_scheduled:
            await self.necrobot.client.send_message(
                cmd.channel,
                'The scheduled time for this match has already been confirmed by both racers. To reschedule, '
                'both racers should first call `.unconfirm`; you will then be able to `.suggest` a new time.')
            return

        # Get the command's author as a NecroUser object
        author_as_necrouser = NecroUser.get_user(necrobot=self.necrobot, discord_id=cmd.author.id)
        if not author_as_necrouser:
            await self.necrobot.client.send_message(
                cmd.channel,
                'Error: {0} is not registered. Please register with `.stream` in the main channel. '
                'If the problem persists, contact CoNDOR Staff.'.format(cmd.author.mention))
            return

        # Check that both racers in the match are registered
        if not match.racer_1 or not match.racer_2 \
                or not match.racer_1.discord_id or not match.racer_2.discord_id:
            await self.necrobot.client.send_message(
                cmd.channel,
                'Error: At least one of the racers in this match is not registered, and needs to call '
                '`.register` in the main channel. (To check if you are registered, you can call `.userinfo '
                '<discord name>`. Use quotes around your discord name if it contains a space.)')
            return

        # Check that the command author is racing in the match
        if not match.racing_in_match(author_as_necrouser):
            await self.necrobot.client.send_message(
                cmd.channel,
                'Error: {0} does not appear to be one of the racers in this match. '
                'If this is in error, contact CoNDOR Staff.'.format(cmd.author.mention))
            return

        # Get the racer's timezone
        if author_as_necrouser.timezone is None:
            await self.necrobot.client.send_message(
                cmd.channel,
                '{0}: Please register a timezone with `.timezone`.'.format(cmd.author.mention))
            return

        # Parse the inputs as a datetime
        try:
            suggested_time_utc = dateparse.parse_datetime(cmd.arg_string, author_as_necrouser.timezone)
        except ParseException as e:
            await self.necrobot.client.send_message(
                cmd.channel,
                'Failed to parse your input as a time ({0}).'.format(e))
            return

        # Check if the scheduled time is in the past
        utcnow = pytz.utc.localize(datetime.datetime.utcnow())
        time_until = suggested_time_utc - utcnow
        if not time_until.total_seconds() > 0:
            await self.necrobot.client.send_message(
                cmd.channel,
                '{0}: Error: The time you are suggesting for the match appears to be in the past.'.format(
                    cmd.author.mention))
            return

        # TODO: Code to check for "deadlines" on suggested times.

        # Suggest the time and confirm
        match.suggest_time(suggested_time_utc)
        match.confirm_time(author_as_necrouser)

        # Output what we did
        for racer in match.racers:
            if racer.member is not None:
                if racer.timezone is not None:
                    if racer == author_as_necrouser:
                        await self.necrobot.client.send_message(
                            cmd.channel,
                            '{0}: You\'ve suggested the match be scheduled for {1}. Waiting for the other '
                            'racer to `.confirm`.'.format(
                                racer.member.mention,
                                timestr.str_full_12h(racer.timezone.normalize(suggested_time_utc))))
                    else:
                        await self.necrobot.client.send_message(
                            cmd.channel,
                            '{0}: This match is suggested to be scheduled for {1}. Please confirm with '
                            '`.confirm`.'.format(
                                racer.member.mention,
                                timestr.str_full_12h(racer.timezone.normalize(suggested_time_utc))))
                else:
                    await self.necrobot.client.send_message(
                        cmd.channel,
                        '{0}: A match time has been suggested; please confirm with `.confirm`. I also suggest '
                        'you register a timezone (use `.timezone`), so I can convert to your local time.'.format(
                            racer.member.mention))


class Unconfirm(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'unconfirm')
        self.help_text = 'Remove your confirmation. If all racers have already confirmed, then all racers must ' \
                         '`.unconfirm` for the match to be unscheduled.'

    async def _do_execute(self, cmd):
        pass


# Admin matchroom commands
class ForceBegin(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-begin')
        self.help_text = 'Force the match to begin now.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        pass


class ForceConfirm(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-confirm')
        self.help_text = 'Force all racers to confirm the suggested time.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        pass


class ForceReschedule(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-reschedule')
        self.help_text = 'Forces the race to be rescheduled for a specific UTC time. Usage same as `.suggest`, e.g., ' \
                         '`.f-reschedule February 18 2:30p`, except that the timezone is always taken to be UTC. ' \
                         'This command unschedules the match and `.suggests` a new time. Use `.f-confirm` after ' \
                         'if you wish to automatically have the racers confirm this new time.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        pass


class ForceUnschedule(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-unschedule')
        self.help_text = 'Forces the race to be unscheduled.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        pass
