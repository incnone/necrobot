import datetime

import pytz

from necrobot.botbase.command import CommandType
from necrobot.database import necrodb
from necrobot.race.match import matchroom
from necrobot.user.necrouser import NecroUser
from necrobot.util import timestr
from necrobot.util.parse import dateparse
from necrobot.util.parse.exception import ParseException


# Matchroom commands
class Confirm(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'confirm')
        self.help_text = 'Confirm that you agree to the suggested time for this match.'

    async def _do_execute(self, cmd):
        match = self.bot_channel.match
        if not match.has_suggested_time:
            await self.client.send_message(
                cmd.channel,
                'Error: A scheduled time for this match has not been suggested. Use `.suggest` to suggest a time.')
            return

        author_as_necrouser = NecroUser.get_user(discord_id=int(cmd.author.id))
        if author_as_necrouser is None:
            await self.client.send_message(
                cmd.channel,
                'Error: {0} is not registered. Please register with `.register` in the main channel. '
                'If the problem persists, contact CoNDOR Staff.'.format(cmd.author.mention))
            return

        if match.is_confirmed_by(author_as_necrouser):
            await self.client.send_message(
                cmd.channel,
                '{0}: You\'ve already confirmed this time.'.format(cmd.author.mention))
            return

        match.confirm_time(author_as_necrouser)
        necrodb.write_match(match)
        await self.client.send_message(
            cmd.channel,
            '{0}: Confirmed acceptance of match time {1}.'.format(
                cmd.author.mention,
                timestr.str_full_12h(match.suggested_time.astimezone(author_as_necrouser.timezone))))

        if match.is_scheduled:
            await self.client.send_message(
                cmd.channel,
                'The match has been officially scheduled.')


class Suggest(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'suggest')
        self.help_text = 'Suggest a time to schedule a match (your local time). Examples:\n' \
                         '   `.suggest Feb 18 17:30`' \
                         '   `.suggest Thursday 8p`' \
                         '   `.suggest today 9:15pm`' \
                         '   `.suggest now'

    async def _do_execute(self, cmd):
        match = self.bot_channel.match

        # Check for match already being confirmed
        if match.is_scheduled:
            await self.client.send_message(
                cmd.channel,
                'The scheduled time for this match has already been confirmed by both racers. To reschedule, '
                'both racers should first call `.unconfirm`; you will then be able to `.suggest` a new time.')
            return

        # Get the command's author as a NecroUser object
        author_as_necrouser = NecroUser.get_user(discord_id=cmd.author.id)
        if not author_as_necrouser:
            await self.client.send_message(
                cmd.channel,
                'Error: {0} is not registered. Please register with `.stream` in the main channel. '
                'If the problem persists, contact CoNDOR Staff.'.format(cmd.author.mention))
            return

        # Check that both racers in the match are registered
        if not match.racer_1 or not match.racer_2 \
                or not match.racer_1.discord_id or not match.racer_2.discord_id:
            await self.client.send_message(
                cmd.channel,
                'Error: At least one of the racers in this match is not registered, and needs to call '
                '`.register` in the main channel. (To check if you are registered, you can call `.userinfo '
                '<discord name>`. Use quotes around your discord name if it contains a space.)')
            return

        # Check that the command author is racing in the match
        if not match.racing_in_match(author_as_necrouser):
            await self.client.send_message(
                cmd.channel,
                'Error: {0} does not appear to be one of the racers in this match. '
                'If this is in error, contact CoNDOR Staff.'.format(cmd.author.mention))
            return

        # Get the racer's timezone
        if author_as_necrouser.timezone is None:
            await self.client.send_message(
                cmd.channel,
                '{0}: Please register a timezone with `.timezone`.'.format(cmd.author.mention))
            return

        # Parse the inputs as a datetime
        try:
            suggested_time_utc = dateparse.parse_datetime(cmd.arg_string, author_as_necrouser.timezone)
        except ParseException as e:
            await self.client.send_message(
                cmd.channel,
                'Failed to parse your input as a time ({0}).'.format(e))
            return

        # Check if the scheduled time is in the past
        utcnow = pytz.utc.localize(datetime.datetime.utcnow())
        time_until = suggested_time_utc - utcnow
        if not time_until.total_seconds() > 0:
            await self.client.send_message(
                cmd.channel,
                '{0}: Error: The time you are suggesting for the match appears to be in the past.'.format(
                    cmd.author.mention))
            return

        # TODO: Code to check for "deadlines" on suggested times.

        # Suggest the time and confirm
        match.suggest_time(suggested_time_utc)
        match.confirm_time(author_as_necrouser)
        necrodb.write_match(match)

        # Output what we did
        for racer in match.racers:
            if racer.member is not None:
                if racer.timezone is not None:
                    if racer == author_as_necrouser:
                        await self.client.send_message(
                            cmd.channel,
                            '{0}: You\'ve suggested the match be scheduled for {1}. Waiting for the other '
                            'racer to `.confirm`.'.format(
                                racer.member.mention,
                                timestr.str_full_12h(racer.timezone.normalize(suggested_time_utc))))
                    else:
                        await self.client.send_message(
                            cmd.channel,
                            '{0}: This match is suggested to be scheduled for {1}. Please confirm with '
                            '`.confirm`.'.format(
                                racer.member.mention,
                                timestr.str_full_12h(racer.timezone.normalize(suggested_time_utc))))
                else:
                    await self.client.send_message(
                        cmd.channel,
                        '{0}: A match time has been suggested; please confirm with `.confirm`. I also suggest '
                        'you register a timezone (use `.timezone`), so I can convert to your local time.'.format(
                            racer.member.mention))

        await self.bot_channel.update()


class Unconfirm(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'unconfirm')
        self.help_text = 'Remove your confirmation. If all racers have already confirmed, then all racers must ' \
                         '`.unconfirm` for the match to be unscheduled.'

    async def _do_execute(self, cmd):
        match = self.bot_channel.match

        author_as_necrouser = NecroUser.get_user(discord_id=int(cmd.author.id))
        if author_as_necrouser is None:
            await self.client.send_message(
                cmd.channel,
                'Error: {0} is not registered. Please register with `.register` in the main channel. '
                'If the problem persists, contact CoNDOR Staff.'.format(cmd.author.mention))
            return

        if not match.is_confirmed_by(author_as_necrouser):
            await self.client.send_message(
                cmd.channel,
                '{0}: You haven\'t yet confirmed the suggested time.'.format(cmd.author.mention))
            return

        match_was_scheduled = match.is_scheduled
        match.unconfirm_time(author_as_necrouser)
        necrodb.write_match(match)

        # if match was scheduled...
        if match_was_scheduled:
            # ...and still is
            if match.is_scheduled:
                await self.client.send_message(
                    cmd.channel,
                    '{0} wishes to remove the current scheduled time. The other racer must also '
                    '`.unconfirm`.'.format(cmd.author.mention))
            # ...and now is not
            else:
                await self.client.send_message(
                    cmd.channel,
                    'The match has been unscheduled. Please `.suggest` a new time when one has been agreed upon.')
        # if match was not scheduled
        else:
            await self.client.send_message(
                cmd.channel,
                '{0} has unconfirmed the current suggested time.'.format(cmd.author.mention))

        await self.bot_channel.update()


# Admin matchroom commands
class ForceBegin(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-begin')
        self.help_text = '[Admin only] Force the match to begin now.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        match = self.bot_channel.match
        match.suggest_time(datetime.datetime.utcnow())
        match.force_confirm()
        necrodb.write_match(match)
        await self.bot_channel.update()


class ForceConfirm(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-confirm')
        self.help_text = '[Admin only] Force all racers to confirm the suggested time.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        match = self.bot_channel.match
        if not match.is_scheduled:
            await self.client.send_message(
                cmd.channel,
                'Error: A scheduled time for this match has not been suggested. '
                'One of the racers should use `.suggest` to suggest a time.')
            return

        match.force_confirm()
        necrodb.write_match(match)

        await self.client.send_message(
            cmd.channel,
            '{0} has forced confirmation of match time: {1}.'.format(
                cmd.author.mention, timestr.str_full_12h(match.time)))
        await self.bot_channel.update()


class ForceReschedule(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-reschedule')
        self.help_text = '[Admin only] Forces the race to be rescheduled for a specific UTC time. Usage same as ' \
                         '`.suggest`, e.g., `.f-reschedule February 18 2:30p`, except that the timezone is always ' \
                         'taken to be UTC. This command unschedules the match and `.suggests` a new time. Use ' \
                         '`.f-confirm` after if you wish to automatically have the racers confirm this new time.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        # Parse the inputs as a datetime
        try:
            suggested_time_utc = dateparse.parse_datetime(cmd.arg_string, pytz.utc)
        except ParseException as e:
            await self.client.send_message(
                cmd.channel,
                'Failed to parse your input as a time ({0}).'.format(e))
            return

        match = self.bot_channel.match

        # Suggest the time and confirm
        match.suggest_time(suggested_time_utc)
        necrodb.write_match(match)

        # Output what we did
        for racer in match.racers:
            if racer.member is not None:
                if racer.timezone is not None:
                    await self.client.send_message(
                        cmd.channel,
                        '{0}: This match is suggested to be scheduled for {1}. Please confirm with '
                        '`.confirm`.'.format(
                            racer.member.mention,
                            timestr.str_full_12h(racer.timezone.normalize(suggested_time_utc))))
                else:
                    await self.client.send_message(
                        cmd.channel,
                        '{0}: A match time has been suggested; please confirm with `.confirm`. I also suggest '
                        'you register a timezone (use `.timezone`), so I can convert to your local time.'.format(
                            racer.member.mention))

        await self.bot_channel.update()


class ForceUnschedule(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-unschedule')
        self.help_text = '[Admin only] Forces the race to be unscheduled.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        match = self.bot_channel.match
        match.force_unconfirm()
        necrodb.write_match(match)

        await self.client.send_message(
            cmd.channel,
            'The match has been unscheduled. Please `.suggest` a new time.')

        await self.bot_channel.update()


class Postpone(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'postpone')
        self.help_text = '[Admin only] Postpones the match. An admin can resume with `.f-begin`.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        match = self.bot_channel.match
        if not match.is_scheduled:
            await self.client.send_message(
                cmd.channel,
                '{0}: This match hasn\'t been scheduled.'.format(cmd.author.mention))
            return

        match.force_unconfirm()
        necrodb.write_match(match)
        await self.client.send_message(
            cmd.channel,
            'The match has been postponed. An admin can resume with `.forcebeginmatch`, or the racers can '
            '`.suggest` a new time as usual.')
        await self.bot_channel.update()


class RebootRoom(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'rebootroom')
        self.help_text = '[Admin only] Reboots the match room (may help solve bugs).'
        self.admin_only = True

    async def _do_execute(self, cmd):
        await matchroom.make_match_room(match=self.bot_channel.match)
        await self.client.send_message(
            cmd.channel,
            'Room rebooted.')


class SetMatchType(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'setmatchtype')
        self.help_text = '[Admin only] Set the type of the match. Use `.setmatchtype repeat X` to make the match be ' \
                         'racers play X races; use `.setmatchtype bestof Y` to make the match a best-of-Y.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        if len(cmd.args) != 2:
            await self.client.send_message(
                cmd.channel,
                'Error: Wrong number of arguments for `.setmatchtype`.')

        try:
            num = int(cmd.args[1])
            matchtype = cmd.args[0].lstrip('-')

            match = self.bot_channel.match

            if matchtype.lower() == 'repeat':
                match.set_repeat(num)
                necrodb.write_match(match)
                await self.client.send_message(
                    cmd.channel,
                    'This match has been set to be a repeat-{0}.'.format(num))
            elif matchtype.lower() == 'bestof':
                match.set_best_of(num)
                necrodb.write_match(match)
                await self.client.send_message(
                    cmd.channel,
                    'This match has been set to be a best-of-{0}.'.format(num))
            else:
                await self.client.send_message(
                    cmd.channel,
                    'Error: I don\'t recognize the argument {0}.'.format(type))
                return

            await self.bot_channel.update()

        except ValueError:
            await self.client.send_message(
                cmd.channel,
                'Error: Couldn\'t parse {0} as a number.'.format(cmd.args[1]))


class Update(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'update')
        self.help_text = '[Admin only] Update the match room (may help solve bugs).'
        self.admin_only = True

    async def _do_execute(self, cmd):
        await self.bot_channel.update()
