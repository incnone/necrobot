import datetime
import os
import asyncio
import pytz

import necrobot.exception
from necrobot.botbase.command import Command
from necrobot.botbase.commandtype import CommandType
from necrobot.botbase.necroevent import NEDispatch
from necrobot.config import Config
from necrobot.league import leaguedb
from necrobot.league.leaguemgr import LeagueMgr
from necrobot.match import matchutil, cmd_matchmake, matchinfo, matchdb, matchchannelutil
from necrobot.user import userlib
from necrobot.util import server
from necrobot.util.parse import dateparse
from necrobot.util import console


class ScrubDatabase(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'scrubdatabase')
        self.help_text = 'Deletes matches without a current channel and with no played races from the database.'
        self.admin_only = True

    async def _do_execute(self, cmd: Command):
        await matchdb.scrub_unchanneled_unraced_matches()
        matchutil.invalidate_cache()
        await cmd.channel.send(
            'Database scrubbed.'
        )


class CloseAllMatches(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'closeall', 'closeallmatches')
        self.help_text = 'Close all match rooms. Use `{0} nolog` to close all rooms without writing ' \
                         'logs (much faster, but no record will be kept of room chat).' \
                         .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Close all match rooms.'

    async def _do_execute(self, cmd: Command):
        log = 'nolog' not in cmd.args

        status_message = await cmd.channel.send(
            'Closing all match channels...'
        )
        await self.client.send_typing(cmd.channel)

        await matchchannelutil.delete_all_match_channels(log=log)

        await self.client.edit_message(
            status_message,
            'Closing all match channels... done.'
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

        status_message = await cmd.channel.send(
            'Closing all completed match channels...'
        )

        async with cmd.channel.typing():
            await matchchannelutil.delete_all_match_channels(log=log, completed_only=True)

        await status_message.edit(
            'Closing all completed match channels... done.'
        )


class Deadline(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'deadline')
        self.help_text = 'Get the deadline for scheduling matches.'
        self.admin_only = True

    async def _do_execute(self, cmd: Command):
        if LeagueMgr().league is None:
            await cmd.channel.send(
                'Error: No league set.'
            )
            return

        deadline_str = LeagueMgr().league.deadline

        if deadline_str is None:
            await cmd.channel.send(
                'No deadline is set for the current league.'
            )
            return

        try:
            deadline = dateparse.parse_datetime(deadline_str)
        except necrobot.exception.ParseException as e:
            await cmd.channel.send(str(e))
            return

        await cmd.channel.send(
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
            await cmd.channel.send(
                'Wrong number of args for `{0}`.'.format(self.mention)
            )
            return

        username = cmd.args[0]
        user = await userlib.get_user(any_name=username)
        if user is None:
            await cmd.channel.send(
                "Couldn't find a user with name `{0}`.".format(cmd.args[0])
            )
            return

        matches = await matchchannelutil.get_matches_with_channels(racer=user)
        deleted_any = False
        for the_match in matches:
            channel = server.find_channel(channel_id=the_match.channel_id)
            if channel is not None:
                await channel.delete()
                await matchutil.delete_match(match_id=the_match.match_id)
                deleted_any = True

        if deleted_any:
            await cmd.channel.send(
                "Dropped `{0}` from all their current matches.".format(user.display_name)
            )
        else:
            await cmd.channel.send(
                "Couldn't find any current matches for `{0}`.".format(user.display_name)
            )


class GetCurrentEvent(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'eventinfo')
        self.help_text = 'Get the identifier and name of the current CoNDOR event.' \
            .format(self.mention)
        self.admin_only = True

    async def _do_execute(self, cmd: Command):
        league = LeagueMgr().league
        if league is None:
            await cmd.channel.send(
                'Error: The current event (`{0}`) does not exist.'.format(Config.LEAGUE_NAME)
            )
            return

        await cmd.channel.send(
            '```\n'
            'Current event:\n'
            '    ID: {0}\n'
            '  Name: {1}\n'
            '```'.format(league.schema_name, league.name)
        )


class GetMatchRules(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'rules')
        self.help_text = "Get the current event's default match rules."
        self.admin_only = True

    async def _do_execute(self, cmd: Command):
        league = LeagueMgr().league
        if league is None:
            await cmd.channel.send(
                'Error: The current event (`{0}`) does not exist.'.format(Config.LEAGUE_NAME)
            )
            return

        await cmd.channel.send(
            'Current event (`{0}`) default rules: {1}'.format(league.schema_name, league.match_info.format_str)
        )


class ForceMakeMatch(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-makematch')
        self.help_text = 'Create a new match room between two racers with ' \
                         '`{0} racer_1_name racer_2_name`.'.format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Create new match room.'

    async def _do_execute(self, cmd):
        # Parse arguments
        if len(cmd.args) != 2:
            await cmd.channel.send(
                'Error: Wrong number of arguments for `{0}`.'.format(self.mention))
            return

        league = LeagueMgr().league
        if league is None:
            await cmd.channel.send(
                'Error: The current event (`{0}`) does not exist.'.format(Config.LEAGUE_NAME)
            )
            return

        new_match = await cmd_matchmake.make_match_from_cmd(
            cmd=cmd,
            cmd_type=self,
            racer_names=[cmd.args[0], cmd.args[1]],
            match_info=league.match_info
        )
        if new_match is not None:
            await NEDispatch().publish(event_type='create_match', match=new_match)


class MakeMatch(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'makematch')
        self.help_text = '`{0}` username: Make a new match between yourself and the given user.'.format(self.mention)

    @property
    def short_help_text(self):
        return 'Create new match room.'

    async def _do_execute(self, cmd):
        # Parse arguments
        if len(cmd.args) != 1:
            await cmd.channel.send(
                'Error: Wrong number of arguments for `{0}`.'.format(self.mention))
            return

        league = LeagueMgr().league
        if league is None:
            await cmd.channel.send(
                'Error: The current event (`{0}`) does not exist.'.format(Config.LEAGUE_NAME)
            )
            return

        # Make the match
        try:
            new_match = await cmd_matchmake.make_match_from_cmd(
                cmd=cmd,
                cmd_type=self,
                racer_names=[cmd.author.display_name, cmd.args[0]],
                match_info=league.match_info,
                allow_duplicates=False
            )
        except necrobot.exception.DuplicateMatchException:
            await cmd.channel.send(
                'A match between `{r1}` and `{r2}` already exists! Contact incnone if this is in error.'.format(
                    r1=cmd.author.display_name,
                    r2=cmd.args[0]
                )
            )
            return

        if new_match is not None:
            await NEDispatch().publish(event_type='create_match', match=new_match)


class MakeMatchesFromFile(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'makematchesfromfile')
        self.help_text = '`{0}` filename: Make a set of matches as given in the filename. The file should be a .csv ' \
            'file, one match per row, whose rows are of the form `racer_1_name,racer_2_name`.'.format(self.mention)

    @property
    def short_help_text(self):
        return 'Make a set of matches from a file.'

    async def _do_execute(self, cmd):
        if len(cmd.args) != 1:
            await cmd.channel.send(
                'Wrong number of arguments for `{0}`.'.format(self.mention)
            )
            return

        filename = cmd.args[0]
        if not filename.endswith('.csv'):
            await cmd.channel.send(
                'Matchup file should be a `.csv` file.'
            )
            return
        file_path = os.path.join(filename)
        if not os.path.isfile(file_path):
            await cmd.channel.send(
                'Cannot find file `{}`.'.format(filename)
            )
            return

        match_info = LeagueMgr().league.match_info
        status_message = await cmd.channel.send(
            'Creating matches from file `{0}`... (Reading file)'.format(filename)
        )

        with cmd.channel.typing():
            # Store file data
            desired_match_pairs = []
            with open(file_path) as file:
                for line in file:
                    racernames = line.rstrip('\n').split(',')
                    desired_match_pairs.append((racernames[0].lower(), racernames[1].lower(),))

            # Find all racers
            all_racers = dict()
            for racerpair in desired_match_pairs:
                all_racers[racerpair[0]] = None
                all_racers[racerpair[1]] = None

            await userlib.fill_user_dict(all_racers)
            console.debug('MakeMatchesFromFile: Filled user dict: {}'.format(all_racers))

            # Create Match objects
            matches = []
            not_found_matches = []

            async def make_single_match(racers):
                console.debug('MakeMatchesFromFile: Making match {0}-{1}'.format(racers[0], racers[1]))
                racer_1 = all_racers[racers[0]]
                racer_2 = all_racers[racers[1]]
                if racer_1 is None or racer_2 is None:
                    console.warning('Couldn\'t find racers for match {0}-{1}.'.format(
                        racers[0], racers[1]
                    ))
                    not_found_matches.append('`{0}`-`{1}`'.format(racers[0], racers[1]))
                    return

                new_match = await matchutil.make_match(
                    register=True,
                    racer_1_id=racer_1.user_id,
                    racer_2_id=racer_2.user_id,
                    match_info=match_info,
                    autogenned=True
                )
                if new_match is None:
                    console.debug('MakeMatchesFromFile: Match {0}-{1} not created.'.format(racers[0], racers[1]))
                    not_found_matches.append('{0}-{1}'.format(racers[0], racers[1]))
                    return

                matches.append(new_match)
                console.debug('MakeMatchesFromFile: Created {0}-{1}'.format(
                    new_match.racer_1.rtmp_name, new_match.racer_2.rtmp_name)
                )

            for racer_pair in desired_match_pairs:
                await make_single_match(racer_pair)

            matches = sorted(matches, key=lambda m: m.matchroom_name)

            await status_message.edit(
                'Creating matches from file `{0}`... (Creating race rooms)'.format(filename)
            )
            console.debug('MakeMatchesFromFile: Matches to make: {0}'.format(matches))

            # Create match channels
            for match in matches:
                console.info('MakeMatchesFromFile: Creating {0}...'.format(match.matchroom_name))
                new_room = await matchchannelutil.make_match_room(match=match, register=False)
                await new_room.send_channel_start_text()

            # Report on uncreated matches
            uncreated_str = ''
            for match_str in not_found_matches:
                uncreated_str += match_str + ', '
            if uncreated_str:
                uncreated_str = uncreated_str[:-2]

            if uncreated_str:
                report_str = 'The following matches were not made: {0}'.format(uncreated_str)
            else:
                report_str = 'All matches created successfully.'

        await status_message.edit(
            'Creating matches from file `{0}`... done. {1}'.format(filename, report_str)
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
            await cmd.channel.send(
                'Didn\'t find any scheduled matches!')
            return

        if len(matches) >= num_to_show:
            latest_shown = matches[num_to_show - 1]
            upcoming_matches = []
            for match in matches:
                if match.suggested_time - latest_shown.suggested_time < datetime.timedelta(minutes=10) \
                        or match.suggested_time - utcnow < datetime.timedelta(hours=1, minutes=5):
                    upcoming_matches.append(match)
        else:
            upcoming_matches = matches

        await cmd.channel.send(
            await matchutil.get_nextrace_displaytext(upcoming_matches)
        )


class Register(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'register')
        self.help_text = 'Register for the current event.'.format(self.mention)

    async def _do_execute(self, cmd: Command):
        user = await userlib.get_user(discord_id=int(cmd.author.id))
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
            await cmd.channel.send(
                'Wrong number of arguments for `{0}`.'.format(self.mention)
            )
            return

        schema_name = cmd.args[0].lower()
        try:
            await LeagueMgr().create_league(schema_name=schema_name)
        except necrobot.exception.LeagueAlreadyExists as e:
            await cmd.channel.send(
                'Error: Schema `{0}`: {1}'.format(schema_name, e)
            )
            return
        except necrobot.exception.InvalidSchemaName:
            await cmd.channel.send(
                'Error: `{0}` is an invalid schema name. (`a-z`, `A-Z`, `0-9`, `_` and `$` are allowed characters.)'
                .format(schema_name)
            )
            return

        await cmd.channel.send(
            'Registered new CoNDOR event `{0}`, and set it to be the bot\'s current event.'.format(schema_name)
        )


class SetCondorEvent(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'setevent', 'setleague')
        self.help_text = '`{0} schema_name`: Set the bot\'s current event to `schema_name`.' \
            .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Set the bot\'s current CoNDOR event.'

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 1:
            await cmd.channel.send(
                'Wrong number of arguments for `{0}`.'.format(self.mention)
            )
            return

        schema_name = cmd.args[0].lower()
        try:
            await LeagueMgr().set_league(schema_name=schema_name)
        except necrobot.exception.LeagueDoesNotExist:
            await cmd.channel.send(
                'Error: Event `{0}` does not exist.'.format(schema_name)
            )
            return

        league_name = LeagueMgr().league.name
        league_name_str = ' ({0})'.format(league_name) if league_name is not None else ''
        await cmd.channel.send(
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
            await cmd.channel.send(
                'Error: No league set.'
            )
            return

        try:
            deadline = dateparse.parse_datetime(cmd.arg_string)
        except necrobot.exception.ParseException as e:
            await cmd.channel.send(str(e))
            return

        LeagueMgr().league.deadline = cmd.arg_string
        LeagueMgr().league.commit()

        await cmd.channel.send(
            'Set the current league\'s deadline to "{deadline_str}". As of now, this is '
            '{deadline:%b %d (%A) at %I:%M %p (%Z)}.'
            .format(
                deadline_str=cmd.arg_string,
                deadline=deadline
            )
        )


class SetEventName(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'setname')
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
            await cmd.channel.send(
                'Error: The current event (`{0}`) does not exist.'.format(Config.LEAGUE_NAME)
            )
            return

        league.name = cmd.arg_string
        league.commit()

        await cmd.channel.send(
            'Set the name of current CoNDOR event (`{0}`) to {1}.'.format(league.schema_name, league.name)
        )


class SetMatchRules(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'setrules')
        self.help_text = \
            'Set the current event\'s default match rules. Flags:\n' \
            '`bestof X | repeat X`: Set the match to be a best-of-X or a repeat-X.\n' \
            '`charname`: Set the default match character.\n' \
            '`u | s | seed X`: Set the races to be unseeded, seeded, or with a fixed seed.\n' \
            '`custom desc`: Give the matches a custom description.\n' \
            '`nodlc`: Matches are marked as being without the Amplified DLC.'
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Set current event\'s default match rules.'

    async def _do_execute(self, cmd: Command):
        league = LeagueMgr().league
        if league is None:
            await cmd.channel.send(
                'Error: The current event (`{0}`) does not exist.'.format(Config.LEAGUE_NAME)
            )
            return

        try:
            match_info = matchinfo.parse_args(cmd.args)
        except necrobot.exception.ParseException as e:
            await cmd.channel.send(
                'Error parsing inputs: {0}'.format(e)
            )
            return

        league.match_info = match_info
        league.commit()
        await cmd.channel.send(
            'Set the default match rules for `{0}` to {1}.'.format(league.schema_name, match_info.format_str)
        )
