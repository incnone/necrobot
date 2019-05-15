import datetime

import pytz

import necrobot.exception
from necrobot.botbase.command import Command
from necrobot.botbase.commandtype import CommandType
from necrobot.botbase.necroevent import NEDispatch
from necrobot.match import matchdb, matchfindparse
from necrobot.match.matchglobals import MatchGlobals
from necrobot.user import userlib
from necrobot.util import console, server, timestr, writechannel
from necrobot.util.parse import dateparse


# Match-related main-channel commands
class Cawmentate(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'cawmentate', 'commentate', 'cawmmentate')
        self.help_text = 'Register yourself for cawmentary for a given match. Usage is `{0} rtmp1 ' \
                         'rtmn2`, where `rtmp1` and `rtmn2` are the RTMP names of the racers in the match. ' \
                         '(Call `.userinfo` for RTMP names.)'.format(self.mention)

    @property
    def short_help_text(self):
        return 'Register for cawmentary.'

    async def _do_execute(self, cmd):
        await _do_cawmentary_command(cmd, self, add=True)


class Uncawmentate(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'uncawmentate', 'uncommentate', 'uncawmmentate')
        self.help_text = 'Remove yourself as cawmentator for a match. Usage is `{0} rtmp1 rtmp2`.'.format(self.mention)

    @property
    def short_help_text(self):
        return 'Unregister for cawmentary.'

    async def _do_execute(self, cmd):
        await _do_cawmentary_command(cmd=cmd, cmd_type=self, add=False)


class Vod(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'vod')
        self.help_text = 'Add a link to a vod for a given match. Usage is `{0} rtmp1 rtmp2 URL`.'.format(self.mention)

    @property
    def short_help_text(self):
        return 'Add a link to a vod.'

    async def _do_execute(self, cmd):
        # Parse arguments
        if len(cmd.args) < 3:
            await cmd.channel.send(
                'Not enough arguments for `{0}`.'.format(self.mention)
            )
            return

        url = cmd.args[len(cmd.args) - 1]
        cmd.args.pop(len(cmd.args) - 1)
        arg_string = ''
        for arg in cmd.args:
            arg_string += arg + ' '

        try:
            match = await matchfindparse.find_match(arg_string, finished_only=True)
        except necrobot.exception.NecroException as e:
            await cmd.channel.send(
                'Error: {0}.'.format(e)
            )
            return

        author_user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)
        if match.cawmentator_id is None or match.cawmentator_id != author_user.user_id:
            await cmd.channel.send(
                '{0}: You are not the cawmentator for the match {1} (and so cannot add a vod).'
                .format(cmd.author.mention, match.matchroom_name)
            )
            return

        await matchdb.add_vod(match=match, vodlink=url)
        await NEDispatch().publish(event_type='set_vod', match=match, url=url)
        await cmd.channel.send(
            'Added a vod for the match {0}.'.format(match.matchroom_name)
        )


# Matchroom commands
class Confirm(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'confirm')
        self.help_text = 'Confirm that you agree to the suggested time for this match.'

    @property
    def short_help_text(self):
        return 'Confirm suggested match time.'

    async def _do_execute(self, cmd):
        match = self.bot_channel.match
        if not match.has_suggested_time:
            await cmd.channel.send(
                'Error: A scheduled time for this match has not been suggested. Use `.suggest` to suggest a time.')
            return

        author_as_necrouser = await userlib.get_user(discord_id=int(cmd.author.id))
        if author_as_necrouser is None:
            await cmd.channel.send(
                'Error: {0} is not registered. Please register with `.register` in the main channel. '
                'If the problem persists, contact CoNDOR Staff.'.format(cmd.author.mention))
            return

        if match.is_confirmed_by(author_as_necrouser):
            await cmd.channel.send(
                '{0}: You\'ve already confirmed this time.'.format(cmd.author.mention))
            return

        match.confirm_time(author_as_necrouser)
        await cmd.channel.send(
            '{0}: Confirmed acceptance of match time {1}.'.format(
                cmd.author.mention,
                timestr.str_full_12h(match.suggested_time.astimezone(author_as_necrouser.timezone))))

        if match.is_scheduled:
            await NEDispatch().publish('schedule_match', match=match)
            await cmd.channel.send(
                'The match has been officially scheduled.')

        await self.bot_channel.update()


class Contest(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'contest')
        self.help_text = 'Contest the result of the previous race.'

    async def _do_execute(self, cmd):
        await self.bot_channel.contest_last_begun_race()
        if guild.staff_role is not None:
            contest_str = '{0}: The previous race has been marked as contested.'.format(guild.staff_role.mention)
        else:
            contest_str = 'The previous race has been marked as contested.'

        await cmd.channel.send(contest_str)
        contest_str = '`{0}` has contested a race in channel {1}.'.format(cmd.author.display_name, cmd.channel.mention)
        await NEDispatch().publish('notify', message=contest_str)


class GetMatchInfo(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'matchinfo')
        self.help_text = 'Get the current match status.'

    async def _do_execute(self, cmd):
        match = self.bot_channel.match
        if not match.is_registered:
            await cmd.channel.send(
                'Unexpected error (match not registered).'
            )
            return

        match_race_data = await matchdb.get_match_race_data(match.match_id)

        await cmd.channel.send(
            '**{0}** [{2} - {3}] **{1}** ({4})'.format(
                match.racer_1.display_name,
                match.racer_2.display_name,
                match_race_data.r1_wins,
                match_race_data.r2_wins,
                match.format_str
            )
        )


class Suggest(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'suggest')
        # noinspection PyUnresolvedReferences
        self.help_text = 'Suggest a time to schedule a match (your local time). Examples:\n' \
                         '\N{BULLET} `{0} Feb 18 17:30`\n' \
                         '\N{BULLET} `{0} Thursday 8p`\n' \
                         '\N{BULLET} `{0} today 9:15pm`\n' \
                         '\N{BULLET} `{0} now`\n'.format(self.mention)

    @property
    def short_help_text(self):
        return 'Suggest a match time.'

    async def _do_execute(self, cmd):
        match = self.bot_channel.match

        # Check for match already being confirmed
        if match.is_scheduled:
            await cmd.channel.send(
                'The scheduled time for this match has already been confirmed by both racers. To reschedule, '
                'both racers should first call `.unconfirm`; you will then be able to `.suggest` a new time.')
            return

        # Get the command's author as a NecroUser object
        author_as_necrouser = await userlib.get_user(discord_id=int(cmd.author.id))
        if not author_as_necrouser:
            await cmd.channel.send(
                'Error: {0} is not registered. Please register with `.stream` in the main channel. '
                'If the problem persists, contact CoNDOR Staff.'.format(cmd.author.mention))
            return

        # Check that both racers in the match are registered
        if not match.racer_1 or not match.racer_2 \
                or not match.racer_1.discord_id or not match.racer_2.discord_id:
            await cmd.channel.send(
                'Error: At least one of the racers in this match is not registered, and needs to call '
                '`.register` in the main channel. (To check if you are registered, you can call `.userinfo '
                '<discord name>`. Use quotes around your discord name if it contains a space.)')
            return

        # Check that the command author is racing in the match
        if not match.racing_in_match(author_as_necrouser):
            await cmd.channel.send(
                'Error: {0} does not appear to be one of the racers in this match. '
                'If this is in error, contact CoNDOR Staff.'.format(cmd.author.mention))
            return

        # Get the racer's timezone
        if author_as_necrouser.timezone is None:
            await cmd.channel.send(
                '{0}: Please register a timezone with `.timezone`.'.format(cmd.author.mention))
            return

        # Parse the inputs as a datetime
        try:
            suggested_time_utc = dateparse.parse_datetime(cmd.arg_string, author_as_necrouser.timezone)
        except necrobot.exception.ParseException as e:
            await cmd.channel.send(
                'Failed to parse your input as a time ({0}).'.format(e))
            return

        # Check if the scheduled time is in the past
        utcnow = pytz.utc.localize(datetime.datetime.utcnow())
        time_until = suggested_time_utc - utcnow
        if not time_until.total_seconds() >= 0:
            await cmd.channel.send(
                '{0}: Error: The time you are suggesting for the match appears to be in the past.'.format(
                    cmd.author.mention))
            return

        # Check for deadlines on suggested times.
        deadline = MatchGlobals().deadline
        if deadline is not None and suggested_time_utc - deadline > datetime.timedelta(seconds=0):
            await cmd.channel.send(
                'Matches must be scheduled before {deadline:%b %d (%A) at %I:%M %p} UTC'
                .format(deadline=deadline)
            )
            return

        # Suggest the time and confirm
        match.suggest_time(suggested_time_utc)
        match.confirm_time(author_as_necrouser)

        # Output what we did
        for racer in match.racers:
            if racer.member is not None:
                if racer.timezone is not None:
                    if racer == author_as_necrouser:
                        await cmd.channel.send(
                            '{0}: You\'ve suggested the match be scheduled for {1}. Waiting for the other '
                            'racer to `.confirm`.'.format(
                                racer.member.mention,
                                timestr.str_full_12h(racer.timezone.normalize(suggested_time_utc))))
                    else:
                        await cmd.channel.send(
                            '{0}: This match is suggested to be scheduled for {1}. Please confirm with '
                            '`.confirm`.'.format(
                                racer.member.mention,
                                timestr.str_full_12h(racer.timezone.normalize(suggested_time_utc))))
                else:
                    await cmd.channel.send(
                        '{0}: A match time has been suggested; please confirm with `.confirm`. I also suggest '
                        'you register a timezone (use `.timezone`), so I can convert to your local time.'.format(
                            racer.member.mention))

        await self.bot_channel.update()


class Unconfirm(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'unconfirm')
        self.help_text = 'Remove your confirmation. If all racers have already confirmed, then all racers must ' \
                         '`.unconfirm` for the match to be unscheduled.'

    @property
    def short_help_text(self):
        return 'Unconfirm current match time.'

    async def _do_execute(self, cmd):
        match = self.bot_channel.match

        author_as_necrouser = await userlib.get_user(discord_id=int(cmd.author.id))
        if author_as_necrouser is None:
            await cmd.channel.send(
                'Error: {0} is not registered. Please register with `.register` in the main channel. '
                'If the problem persists, contact CoNDOR Staff.'.format(cmd.author.mention))
            return

        if not match.is_confirmed_by(author_as_necrouser):
            await cmd.channel.send(
                '{0}: You haven\'t yet confirmed the suggested time.'.format(cmd.author.mention))
            return

        match_was_scheduled = match.is_scheduled
        match.unconfirm_time(author_as_necrouser)

        # if match was scheduled...
        if match_was_scheduled:
            # ...and still is
            if match.is_scheduled:
                await cmd.channel.send(
                    '{0} wishes to remove the current scheduled time. The other racer must also '
                    '`.unconfirm`.'.format(cmd.author.mention))
            # ...and now is not
            else:
                await cmd.channel.send(
                    'The match has been unscheduled. Please `.suggest` a new time when one has been agreed upon.')
        # if match was not scheduled
        else:
            await cmd.channel.send(
                '{0} has unconfirmed the current suggested time.'.format(cmd.author.mention))

        await self.bot_channel.update()


# Admin matchroom commands
class CancelRace(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'cancelrace', 'forcecancel')
        self.help_text = '`{0} N`: Cancel the `N`-th uncanceled race; `{0}` cancels the current race, if one is ' \
                         'ongoing.'.format(self.mention)
        self.admin_only = True

    async def _do_execute(self, cmd):
        if len(cmd.args) > 1:
            await cmd.channel.send(
                'Too many args for `{0}`.'.format(self.mention)
            )
            return

        if len(cmd.args) == 0:
            if self.bot_channel.current_race.complete:
                await cmd.channel.send(
                    'There is no currently ongoing race. Use `{0} N` to cancel a specific previous race.'
                    .format(self.mention)
                )
                return

            await self.bot_channel.current_race.cancel()

        else:
            try:
                race_number = int(cmd.args[0])
            except ValueError:
                await cmd.channel.send(
                    "Error: couldn't parse {0} as a race number.".format(cmd.args[0])
                )
                return

            success = await self.bot_channel.cancel_race(race_number)
            if success:
                await cmd.channel.send(
                    'Canceled race {0}.'.format(race_number)
                )
            else:
                await cmd.channel.send(
                    'Error: Failed to cancel race {0}.'.format(race_number)
                )


class ChangeWinner(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'changewinner')
        self.help_text = '`{0} N username`: Change the winner for the `N`-th uncanceled race to `username`.' \
                         .format(self.mention)
        self.admin_only = True

    async def _do_execute(self, cmd):
        if len(cmd.args) != 2:
            await cmd.channel.send(
                'Wrong number of args for `{0}`.'.format(self.mention)
            )
            return

        try:
            race_number = int(cmd.args[0])
        except ValueError:
            await cmd.channel.send(
                "Couldn't parse `{0}` as a race number.".format(cmd.args[0])
            )
            return

        winner = None
        winner_name = cmd.args[1]
        match = self.bot_channel.match
        if match.racer_1.name_regex.match(winner_name):
            winner = 1
            winner_name = match.racer_1.display_name
        elif match.racer_2.name_regex.match(winner_name):
            winner = 2
            winner_name = match.racer_2.display_name
        if winner is None:
            await cmd.channel.send(
                "Couldn't identify `{0}` as one of the racers in this match.".format(winner_name)
            )
            return

        success = await matchdb.change_winner(match=match, race_number=race_number, winner=winner)
        if success:
            await cmd.channel.send(
                'Changed the winner of race {0} to `{1}`.'.format(race_number, winner_name)
            )
        else:
            await cmd.channel.send(
                'Error: Failed to change the winner of race {0}.'.format(race_number)
            )


class ForceBegin(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-begin', 'forcebegin', 'forcebeginmatch')
        self.help_text = 'Force the match to begin now.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        match = self.bot_channel.match
        match.suggest_time(pytz.utc.localize(datetime.datetime.utcnow()))
        match.force_confirm()
        await self.bot_channel.update()


class ForceCloseRoom(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-close', 'forceclose')
        self.help_text = 'Close (delete) this match channel. Use `{} nolog` if you do not wish to save a log ' \
                         'of the channel text.'.format(self.mention)
        self.admin_only = True

    async def _do_execute(self, cmd):
        match_id = self.bot_channel.match.match_id
        channel = self.bot_channel.channel

        if 'nolog' not in cmd.args:
            await writechannel.write_channel(
                client=server.client,
                channel=channel,
                outfile_name='{0}-{1}'.format(match_id, channel.name)
            )

        await channel.delete()
        await matchdb.register_match_channel(match_id, None)


class ForceCancelMatch(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-cancelmatch', 'forcecancelmatch')
        self.help_text = 'Cancel this match. Warning: This deletes the race channel.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        match = self.bot_channel.match
        channel = self.bot_channel.channel

        if 'nolog' not in cmd.args:
            await writechannel.write_channel(
                client=server.client,
                channel=channel,
                outfile_name='{0}-{1}'.format(match.match_id, channel.name)
            )

        await matchdb.cancel_match(match)
        await channel.delete()


class ForceConfirm(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-confirm', 'forceconfirm')
        self.help_text = 'Force all racers to confirm the suggested time.'
        self.admin_only = True

    async def _do_execute(self, cmd):
        match = self.bot_channel.match
        if not match.has_suggested_time:
            await cmd.channel.send(
                'Error: A scheduled time for this match has not been suggested. '
                'One of the racers should use `.suggest` to suggest a time.')
            return

        match.force_confirm()
        await NEDispatch().publish('schedule_match', match=match)

        await cmd.channel.send(
            'Forced confirmation of match time: {0}.'.format(
                timestr.str_full_12h(match.suggested_time)))
        await self.bot_channel.update()


class ForceNewRace(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'newrace', 'forcenewrace')
        self.help_text = 'Force the bot to make a new race (the current race will be canceled).'
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Make a new race.'

    async def _do_execute(self, cmd):
        await self.bot_channel.force_new_race()


class ForceRecordRace(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'recordrace', 'forcerecordrace')
        self.help_text = '`{0} winner`: Manually record a race with `winner` as the winner.'.format(self.mention)
        self.admin_only = True

    async def _do_execute(self, cmd):
        if len(cmd.args) != 1:
            await cmd.channel.send(
                'Wrong number of args for `{0}`.'.format(self.mention)
            )
            return

        winner = None
        winner_name = cmd.args[0]
        match = self.bot_channel.match
        if match.racer_1.name_regex.match(winner_name):
            winner = 1
            winner_name = match.racer_1.display_name
        elif match.racer_2.name_regex.match(winner_name):
            winner = 2
            winner_name = match.racer_2.display_name

        if winner is None:
            await cmd.channel.send(
                "Couldn't identify `{0}` as one of the racers in this match.".format(winner_name)
            )
            return

        await self.bot_channel.force_record_race(winner=winner)
        await cmd.channel.send(
            "Force-recorded a race with winner {0}.".format(winner_name)
        )


class ForceReschedule(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-schedule', 'f-reschedule', 'forceschedule', 'forcereschedule')
        self.help_text = 'Forces the race to be scheduled for a specific UTC time. Usage same as ' \
                         '`.suggest`, e.g., `.f-schedule February 18 2:30p`, except that the timezone is always ' \
                         'taken to be UTC. This command unschedules the match and `.suggests` a new time. Use ' \
                         '`.f-confirm` after if you wish to automatically have the racers confirm this new time.'
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Reschedule match.'

    async def _do_execute(self, cmd):
        # Parse the inputs as a datetime
        try:
            suggested_time_utc = dateparse.parse_datetime(cmd.arg_string, pytz.utc)
        except necrobot.exception.ParseException as e:
            await cmd.channel.send(
                'Failed to parse your input as a time ({0}).'.format(e))
            return

        match = self.bot_channel.match

        # Suggest the time and confirm
        match.suggest_time(suggested_time_utc)

        # Output what we did
        for racer in match.racers:
            if racer.member is not None:
                if racer.timezone is not None:
                    await cmd.channel.send(
                        '{0}: This match is suggested to be scheduled for {1}. Please confirm with '
                        '`.confirm`.'.format(
                            racer.member.mention,
                            timestr.str_full_12h(racer.timezone.normalize(suggested_time_utc))
                        )
                    )
                else:
                    await cmd.channel.send(
                        '{0}: A match time has been suggested; please confirm with `.confirm`. I also suggest '
                        'you register a timezone (use `.timezone`), so I can convert to your local time.'.format(
                            racer.member.mention
                        )
                    )

        await self.bot_channel.update()


class Postpone(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'postpone', 'f-unschedule', 'forceunschedule')
        self.help_text = 'Postpones the match. An admin can resume with `.f-begin`.'
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Postpone match.'

    async def _do_execute(self, cmd):
        match = self.bot_channel.match
        if not match.is_scheduled:
            await cmd.channel.send(
                '{0}: This match hasn\'t been scheduled.'.format(cmd.author.mention))
            return

        match.force_unconfirm()
        await self.bot_channel.update()
        await cmd.channel.send(
            'The match has been postponed. An admin can resume with `.forcebeginmatch`, or the racers can '
            '`.suggest` a new time as usual.')


class RebootRoom(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'rebootroom')
        self.help_text = 'Reboots the match room (may help solve bugs).'
        self.admin_only = True

    async def _do_execute(self, cmd):
        await cmd.channel.send(
            'This command is currently deprecated.'
        )
        # await match.matchchannelutil.make_match_room(match=self.bot_channel.match)
        # await self.client.send_message(
        #     cmd.channel,
        #     'Room rebooted.'
        # )


class SetMatchType(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'setmatchtype')
        self.help_text = 'Set the type of the match. Use `.setmatchtype repeat X` to make the match be ' \
                         'racers play X races; use `.setmatchtype bestof Y` to make the match a best-of-Y.'
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Set match type (e.g. best-of-X).'

    async def _do_execute(self, cmd):
        if len(cmd.args) != 2:
            await cmd.channel.send(
                'Error: Wrong number of arguments for `.setmatchtype`.')

        try:
            num = int(cmd.args[1])
        except ValueError:
            await cmd.channel.send(
                'Error: Couldn\'t parse {0} as a number.'.format(cmd.args[1]))
            return

        matchtype = cmd.args[0].lstrip('-')
        match = self.bot_channel.match

        if matchtype.lower() == 'repeat':
            match.set_repeat(num)
            await cmd.channel.send(
                'This match has been set to be a repeat-{0}.'.format(num))
        elif matchtype.lower() == 'bestof':
            match.set_best_of(num)
            await cmd.channel.send(
                'This match has been set to be a best-of-{0}.'.format(num))
        else:
            await cmd.channel.send(
                'Error: I don\'t recognize the argument {0}.'.format(type))
            return

        await self.bot_channel.update()


class Update(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'update', 'forceupdate')
        self.help_text = 'Update the match room (may help solve bugs).'
        self.admin_only = True

    async def _do_execute(self, cmd):
        await self.bot_channel.update()
        await cmd.channel.send(
            'Updated.'
        )


async def _do_cawmentary_command(cmd: Command, cmd_type: CommandType, add: bool):
    # Parse arguments
    try:
        match = await matchfindparse.find_match(cmd.arg_string, finished_only=False)  # Only selects unfinished matches
    except necrobot.exception.NecroException as e:
        await cmd.channel.send(
            'Error: {0}.'.format(e)
        )
        return

    author_user = await userlib.get_user(discord_id=int(cmd.author.id), register=True)

    # Check if the match already has cawmentary
    if add:
        if not match.is_scheduled and not cmd_type.bot_channel.is_admin(cmd.author):
            await cmd.channel.send(
                'Can\'t add commentary for match {matchroom_name}, because it hasn\'t been scheduled yet.'
                .format(matchroom_name=match.matchroom_name)
            )
            return
        if match.cawmentator_id is not None:
            cawmentator_user = await userlib.get_user(user_id=match.cawmentator_id)
            if cawmentator_user is not None:
                await cmd.channel.send(
                    'This match already has a cawmentator ({0}).'.format(cawmentator_user.display_name)
                )
                return
            else:
                console.warning(
                    'Unexpected error in Cawmentate._do_execute(): Couldn\'t find NecroUser for '
                    'cawmentator ID {0}'.format(match.cawmentator_id)
                )
                # No return here; we'll just write over this mystery ID
    else:  # not add
        if match.cawmentator_id is None:
            await cmd.channel.send(
                'No one is registered for cawmentary for the match {0}.'.format(match.matchroom_name)
            )
            return
        elif match.cawmentator_id != author_user.user_id:
            await cmd.channel.send(
                'Error: {0}: You are not the registered cawmentator for {1}.'.format(
                    cmd.author.mention, match.matchroom_name
                )
            )
            return

    # Add/delete the cawmentary
    if add:
        match.set_cawmentator_id(author_user.user_id)
        await NEDispatch().publish(event_type='set_cawmentary', match=match)
        await cmd.channel.send(
            'Added {0} as cawmentary for the match {1}.'.format(
                cmd.author.mention, match.matchroom_name
            )
        )
    else:
        match.set_cawmentator_id(None)
        await NEDispatch().publish(event_type='set_cawmentary', match=match)
        await cmd.channel.send(
            'Removed {0} as cawmentary from the match {1}.'.format(
                cmd.author.mention, match.matchroom_name
            )
        )


