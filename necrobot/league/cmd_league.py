import datetime
import pytz

import necrobot.exception
from necrobot.botbase.command import Command
from necrobot.botbase.commandtype import CommandType
from necrobot.config import Config
from necrobot.database import leaguedb
from necrobot.league.leaguemgr import LeagueMgr
from necrobot.match import matchutil, cmd_match, matchinfo
from necrobot.user import userutil
from necrobot.util.parse import dateparse


class CloseAllMatches(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'closeallmatches')
        self.help_text = 'Close all match rooms. Use `{0} nolog` to close all rooms without writing ' \
                         'logs (much faster, but no record will be kept of room chat).' \
            .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Close all match rooms.'

    async def _do_execute(self, cmd: Command):
        log = not (len(cmd.args) == 1 and cmd.args[0].lstrip('-').lower() == 'nolog')

        await self.client.send_message(
            cmd.channel,
            'Closing all match channels...'
        )
        await self.client.send_typing(cmd.channel)

        await matchutil.delete_all_match_channels(log=log)

        await self.client.send_message(
            cmd.channel,
            'Done closing all match channels.'
        )


class CloseFinished(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'closefinished')
        self.help_text = 'Close all match rooms with completed matches. Use `{0} nolog` to close ' \
                         'without writing logs (much faster, but no record will be kept of room chat).' \
            .format(self.mention)
        self.admin_only = True

    async def _do_execute(self, cmd: Command):
        log = not (len(cmd.args) == 1 and cmd.args[0].lstrip('-').lower() == 'nolog')

        await self.client.send_message(
            cmd.channel,
            'Closing all completed match channels...'
        )
        await self.client.send_typing(cmd.channel)

        await matchutil.delete_all_match_channels(log=log, completed_only=True)

        await self.client.send_message(
            cmd.channel,
            'Done closing all completed match channels.'
        )


class Deadline(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'deadline')
        self.help_text = 'Get the deadline for scheduling matches.'
        self.admin_only = True

    async def _do_execute(self, cmd: Command):
        if LeagueMgr().league is None:
            await self.client.send_message(
                cmd.channel,
                'Error: No league set.'
            )
            return

        deadline_str = LeagueMgr().league.deadline

        if deadline_str is None:
            await self.client.send_message(
                cmd.channel,
                'No deadline is set for the current league.'
            )
            return

        try:
            deadline = dateparse.parse_datetime(deadline_str)
        except necrobot.exception.ParseException as e:
            await self.client.send_message(cmd.channel, str(e))
            return

        await self.client.send_message(
            cmd.channel,
            'The current league deadline is "{deadline_str}". As of now, this is '
            '{deadline:%b %d (%A) at %I:%M %p} (UTC).'
            .format(
                deadline_str=deadline_str,
                deadline=deadline
            )
        )


class DropRacer(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'dropracer')
        self.help_text = '`{0} racername`: Drop a racer from all current match channels and delete the matches. ' \
                         'This does not write logs.'.format(self.mention)
        self.admin_only = True

    async def _do_execute(self, cmd: Command):
        if not len(cmd.args) == 1:
            await self.client.send_message(
                cmd.channel,
                'Wrong number of args for `{0}`.'.format(self.mention)
            )
            return

        username = cmd.args[0]
        user = await userutil.get_user(any_name=username)
        if user is None:
            await self.client.send_message(
                cmd.channel,
                "Couldn't find a user with name `{0}`.".format(cmd.args[0])
            )
            return

        matches = await matchutil.get_matches_with_channels(racer=user)
        deleted_any = False
        for match in matches:
            channel = self.necrobot.find_channel_with_id(match.channel_id)
            if channel is not None:
                await self.client.delete_channel(channel)
                await matchutil.delete_match(match_id=match.match_id)
                deleted_any = True

        if deleted_any:
            await self.client.send_message(
                cmd.channel,
                "Dropped `{0}` from all their current matches.".format(user.bot_name)
            )
        else:
            await self.client.send_message(
                cmd.channel,
                "Couldn't find any current matches for `{0}`.".format(user.bot_name)
            )


class GetCurrentEvent(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'get-current-event')
        self.help_text = 'Get the identifier and name of the current CoNDOR event.' \
            .format(self.mention)
        self.admin_only = True

    async def _do_execute(self, cmd: Command):
        league = LeagueMgr().league
        if league is None:
            await self.client.send_message(
                cmd.channel,
                'Error: The current event (`{0}`) does not exist.'.format(Config.LEAGUE_NAME)
            )
            return

        await self.client.send_message(
            cmd.channel,
            '```\n'
            'Current event:\n'
            '    ID: {0}\n'
            '  Name: {1}\n'
            '```'.format(league.schema_name, league.name)
        )


class GetMatchRules(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'get-match-rules')
        self.help_text = "Get the current event's default match rules."
        self.admin_only = True

    async def _do_execute(self, cmd: Command):
        league = LeagueMgr().league
        if league is None:
            await self.client.send_message(
                cmd.channel,
                'Error: The current event (`{0}`) does not exist.'.format(Config.LEAGUE_NAME)
            )
            return

        await self.client.send_message(
            cmd.channel,
            'Current event (`{0}`) default rules: {1}'.format(league.schema_name, league.match_info.format_str)
        )


class MakeMatch(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'makematch')
        self.help_text = 'Create a new match room between two racers with ' \
                         '`{0} racer_1_name racer_2_name`.'.format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Create new match room.'

    async def _do_execute(self, cmd):
        # Parse arguments
        if len(cmd.args) != 2:
            await self.client.send_message(
                cmd.channel,
                'Error: Wrong number of arguments for `{0}`.'.format(self.mention))
            return

        league = LeagueMgr().league
        if league is None:
            await self.client.send_message(
                cmd.channel,
                'Error: The current event (`{0}`) does not exist.'.format(Config.LEAGUE_NAME)
            )
            return

        await cmd_match.make_match_from_cmd(
            cmd=cmd,
            cmd_type=self,
            racer_names=[cmd.args[0], cmd.args[1]],
            match_info=league.match_info
        )


class NextRace(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'next', 'nextrace', 'nextmatch')
        self.help_text = 'Show upcoming matches.'

    async def _do_execute(self, cmd: Command):
        utcnow = pytz.utc.localize(datetime.datetime.utcnow())
        num_to_show = 3

        matches = await matchutil.get_upcoming_and_current()
        if not matches:
            await self.client.send_message(
                cmd.channel,
                'Didn\'t find any scheduled matches!')
            return

        if len(matches) < num_to_show:
            latest_shown = matches[len(matches) - 1]
            upcoming_matches = []
            for match in matches:
                if match.suggested_time - latest_shown.suggested_time < datetime.timedelta(minutes=10) \
                        or match.suggested_time - utcnow < datetime.timedelta(hours=1, minutes=5):
                    upcoming_matches.append(match)
        else:
            upcoming_matches = matches

        await self.client.send_message(
            cmd.channel,
            await matchutil.get_nextrace_displaytext(upcoming_matches)
        )


class Register(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'register')
        self.help_text = 'Register for the current event.'.format(self.mention)

    async def _do_execute(self, cmd: Command):
        user = await userutil.get_user(discord_id=int(cmd.author.id))
        await leaguedb.register_user(user.user_id)


class RegisterCondorEvent(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'register-condor-event')
        self.help_text = '`{0} schema_name`: Create a new CoNDOR event in the database, and set this to ' \
                         'be the bot\'s current event.' \
            .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Create a new CoNDOR event.'

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                'Wrong number of arguments for `{0}`.'.format(self.mention)
            )
            return

        schema_name = cmd.args[0].lower()
        try:
            await LeagueMgr().create_league(schema_name=schema_name)
        except necrobot.exception.LeagueAlreadyExists as e:
            await self.client.send_message(
                cmd.channel,
                'Error: Schema `{0}`: {1}'.format(schema_name, e)
            )
            return
        except necrobot.exception.InvalidSchemaName:
            await self.client.send_message(
                cmd.channel,
                'Error: `{0}` is an invalid schema name. (`a-z`, `A-Z`, `0-9`, `_` and `$` are allowed characters.)'
                .format(schema_name)
            )
            return

        await self.client.send_message(
            cmd.channel,
            'Registered new CoNDOR event `{0}`, and set it to be the bot\'s current event.'.format(schema_name)
        )


class SetCondorEvent(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'set-condor-event')
        self.help_text = '`{0} schema_name`: Set the bot\'s current event to `schema_name`.' \
            .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Set the bot\'s current CoNDOR event.'

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                'Wrong number of arguments for `{0}`.'.format(self.mention)
            )
            return

        schema_name = cmd.args[0].lower()
        try:
            await LeagueMgr().set_league(schema_name=schema_name)
        except necrobot.exception.LeagueDoesNotExist:
            await self.client.send_message(
                cmd.channel,
                'Error: Event `{0}` does not exist.'.format(schema_name)
            )
            return

        league_name = LeagueMgr().league.name
        league_name_str = ' ({0})'.format(league_name) if league_name is not None else ''
        await self.client.send_message(
            cmd.channel,
            'Set the current CoNDOR event to `{0}`{1}.'.format(schema_name, league_name_str)
        )


class SetDeadline(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'setdeadline')
        self.help_text = '`{0} time`: Set a deadline for scheduling matches (e.g. "friday 12:00"). The given time ' \
                         'will be interpreted in UTC.' \
                         .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Set match scheduling deadline.'

    async def _do_execute(self, cmd: Command):
        if LeagueMgr().league is None:
            await self.client.send_message(
                cmd.channel,
                'Error: No league set.'
            )
            return

        try:
            deadline = dateparse.parse_datetime(cmd.arg_string)
        except necrobot.exception.ParseException as e:
            await self.client.send_message(cmd.channel, str(e))
            return

        LeagueMgr().league.deadline = cmd.arg_string
        LeagueMgr().league.commit()

        await self.client.send_message(
            cmd.channel,
            'Set the current league\'s deadline to "{deadline_str}". As of now, this is '
            '{deadline:%b %d (%A) at %I:%M %p}.'
            .format(
                deadline_str=cmd.arg_string,
                deadline=deadline
            )
        )


class SetEventName(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'set-event-name')
        self.help_text = '`{0} league_name`: Set the name of bot\'s current event. Note: This does not ' \
                         'change or create a new event! Use `.register-condor-event` and `.set-condor-event`.' \
            .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Change current event\'s name.'

    async def _do_execute(self, cmd: Command):
        league = LeagueMgr().league
        if league is None:
            await self.client.send_message(
                cmd.channel,
                'Error: The current event (`{0}`) does not exist.'.format(Config.LEAGUE_NAME)
            )
            return

        league.name = cmd.arg_string
        league.commit()

        await self.client.send_message(
            cmd.channel,
            'Set the name of current CoNDOR event (`{0}`) to {1}.'.format(league.schema_name, league.name)
        )


class SetMatchRules(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'set-match-rules')
        self.help_text = \
            'Set the current event\'s default match rules. Flags:\n' \
            '`-bestof X | -repeat X`: Set the match to be a best-of-X or a repeat-X.\n' \
            '`-c charname`: Set the default match character.\n' \
            '`-u | -s | -seed X`: Set the races to be unseeded, seeded, or with a fixed seed.\n' \
            '`-custom desc`: Give the matches a custom description.\n' \
            '`-nodlc`: Matches are marked as being without the Amplified DLC.'
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Set current event\'s default match rules.'

    async def _do_execute(self, cmd: Command):
        league = LeagueMgr().league
        if league is None:
            await self.client.send_message(
                cmd.channel,
                'Error: The current event (`{0}`) does not exist.'.format(Config.LEAGUE_NAME)
            )
            return

        try:
            match_info = matchinfo.parse_args(cmd.args)
        except necrobot.exception.ParseException as e:
            await self.client.send_message(
                cmd.channel,
                'Error parsing inputs: {0}'.format(e)
            )
            return

        league.match_info = match_info
        league.commit()
        await self.client.send_message(
            cmd.channel,
            'Set the default match rules for `{0}` to {1}.'.format(league.schema_name, match_info.format_str)
        )
