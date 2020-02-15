import asyncio
import datetime
import os
import pytz

import necrobot.exception
from necrobot.botbase.command import Command
from necrobot.botbase.commandtype import CommandType
from necrobot.botbase.necroevent import NEDispatch
from necrobot.league import leaguedb
from necrobot.league import leagueutil
from necrobot.league.leaguemgr import LeagueMgr
from necrobot.match import matchutil, cmd_matchmake, matchinfo, matchchannelutil, matchdb
from necrobot.user import userlib
from necrobot.util import server
from necrobot.util import console


# Match-related main-channel commands
class Cawmentate(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'cawmentate', 'commentate', 'cawmmentate', 'caw')
        self.help_text = 'Register yourself for cawmentary for a given match. Usage is `{0} [league_tag] racer_1 ' \
                         'racer_2`, where `league_tag` is the league for the match, and `racer_1` and `racer_2` are ' \
                         'the racers in the match. ' \
                         .format(self.mention)

    @property
    def short_help_text(self):
        return 'Register for cawmentary.'

    async def _do_execute(self, cmd):
        await _do_cawmentary_command(cmd, self, add=True)


class Uncawmentate(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'uncawmentate', 'uncommentate', 'uncawmmentate', 'uncaw')
        self.help_text = 'Remove yourself as cawmentator for a match. Usage is `{0} [league_tag] racer_1 racer_2`.' \
                         .format(self.mention)

    @property
    def short_help_text(self):
        return 'Unregister for cawmentary.'

    async def _do_execute(self, cmd):
        await _do_cawmentary_command(cmd=cmd, cmd_type=self, add=False)


class Vod(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'vod')
        self.help_text = 'Add a link to a vod for a given match. Usage is `{0} league_tag racer_1 racer_2 URL`.'\
                         .format(self.mention)

    @property
    def short_help_text(self):
        return 'Add a link to a vod.'

    async def _do_execute(self, cmd):
        # Parse arguments
        if len(cmd.args) < 4:
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
            match = await leagueutil.find_match(arg_string, finished_only=True)
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
        async with cmd.channel.typing():
            await matchchannelutil.delete_all_match_channels(log=log)

        await status_message.edit(
            content='Closing all match channels... done.'
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
            content='Closing all completed match channels... done.'
        )


class DropRacer(CommandType):
    # TODO: Update this command for multiple leagues (so that racers can be dropped from a single league only)
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'dropracer')
        self.help_text = '`{0} racername`: Drop a racer from all current match channels and delete those matches. ' \
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


class ForceMakeMatch(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'f-makematch')
        self.help_text = 'Create a new match room between two racers with ' \
                         '`{0} league_tag racer_1_name racer_2_name`.'.format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Create new match room.'

    async def _do_execute(self, cmd):
        # Parse arguments
        if len(cmd.args) != 3:
            await cmd.channel.send(
                'Error: Wrong number of arguments for `{0}`.'.format(self.mention))
            return

        league_tag = cmd.args[0].lower()
        try:
            league = await LeagueMgr().get_league(league_tag)
        except necrobot.exception.LeagueDoesNotExist:
            await cmd.channel.send(
                'Error: The league with tag `{0}` does not exist.'.format(league_tag)
            )
            return

        new_match = await cmd_matchmake.make_match_from_cmd(
            cmd=cmd,
            racer_names=[cmd.args[1], cmd.args[2]],
            match_info=league.match_info,
            league_tag=league_tag
        )
        if new_match is not None:
            await NEDispatch().publish(event_type='create_match', match=new_match)


class GetLeagueInfo(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'leagueinfo')
        self.help_text = '`{0}` league_tag: Display the given league\'s info.'.format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Get league info.'

    async def _do_execute(self, cmd):
        if len(cmd.args) != 1:
            await cmd.channel.send('Error: Wrong number of arguments for `{0}`.'.format(self.mention))
            return

        league_tag = cmd.args[0].lower()
        try:
            league = await LeagueMgr().get_league(league_tag=league_tag)
        except necrobot.exception.LeagueDoesNotExist:
            await cmd.channel.send('Error: League `{0}` does not exist.'.format(league_tag))
            return

        await cmd.channel.send(
            '```\n'
            '{name}\n'
            '     Tag: {tag}\n'
            '  Format: {match_info}\n'
            '```'.format(
                name=league.name,
                tag=league.tag,
                match_info=league.match_info.format_str
            )
        )


class MakeLeague(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'makeleague')
        self.help_text = '`{0}` league_tag: Make a new league with the given tag. Tags must be short. ' \
                         'Example: `.makeleague coh`.' \
                         .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Create new league.'

    async def _do_execute(self, cmd):
        if len(cmd.args) != 1:
            await cmd.channel.send('Error: Wrong number of arguments for `{0}`.'.format(self.mention))
            return

        league_tag = cmd.args[0].lower()
        # TODO implement this check properly
        if len(league_tag) > 8:
            await cmd.channel.send('Error: Tag `{0}` is too long.'.format(league_tag))
            return

        try:
            await LeagueMgr.make_league(league_tag=league_tag, league_name=league_tag)
        except necrobot.exception.LeagueAlreadyExists:
            await cmd.channel.send('Error: The league tag `{0}` already exists.'.format(league_tag))
            return

        await cmd.channel.send('League with tag `{0}` created.'.format(league_tag))


class MakeMatch(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'makematch')
        self.help_text = '`{0} league_tag username`: Make a new match in the given league between yourself and the ' \
                         'given user.' \
                         .format(self.mention)

    @property
    def short_help_text(self):
        return 'Create new match room.'

    async def _do_execute(self, cmd):
        # Parse arguments
        if len(cmd.args) != 2:
            await cmd.channel.send(
                'Error: Wrong number of arguments for `{0}`.'.format(self.mention))
            return

        league_tag = cmd.args[0].lower()
        try:
            league = await LeagueMgr().get_league(league_tag)
        except necrobot.exception.LeagueDoesNotExist:
            await cmd.channel.send(
                'Error: League with tag `{0}` does not exist.'.format(league_tag))
            return

        # Make the match
        # TODO Check for duplicates within-league
        other_racer_name = cmd.args[1]
        try:
            new_match = await cmd_matchmake.make_match_from_cmd(
                cmd=cmd,
                racer_members=[cmd.author],
                racer_names=[other_racer_name],
                match_info=league.match_info,
                league_tag=league_tag,
                allow_duplicates=True
            )
        except necrobot.exception.DuplicateMatchException:
            await cmd.channel.send(
                'A match between `{r1}` and `{r2}` already exists! Contact incnone if this is in error.'.format(
                    r1=cmd.author.display_name,
                    r2=other_racer_name
                )
            )
            return

        if new_match is not None:
            await NEDispatch().publish(event_type='create_match', match=new_match)


class MakeMatchesFromFile(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'makematchesfromfile')
        self.help_text = '`{0} league_tag filename`: Make a set of matches as given in the filename. The file should ' \
                         'be a .csv file, one match per row, whose rows are of the form `racer_1_name,racer_2_name`.' \
                         .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Make a set of matches from a file.'

    async def _do_execute(self, cmd):
        if len(cmd.args) != 2:
            await cmd.channel.send(
                'Wrong number of arguments for `{0}`.'.format(self.mention)
            )
            return

        league_tag = cmd.args[0].lower()
        try:
            league = await LeagueMgr().get_league(league_tag)
        except necrobot.exception.LeagueDoesNotExist:
            await cmd.channel.send(
                'Error: League with tag `{0}` does not exist.'.format(league_tag))
            return

        filename = cmd.args[1]
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

        match_info = league.match_info
        status_message = await cmd.channel.send(
            'Creating matches from file `{0}`... (Reading file)'.format(filename)
        )

        async with cmd.channel.typing():
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
                    league_tag=league_tag,
                    autogenned=True
                )
                if new_match is None:
                    console.debug('MakeMatchesFromFile: Match {0}-{1} not created.'.format(racers[0], racers[1]))
                    not_found_matches.append('{0}-{1}'.format(racers[0], racers[1]))
                    return

                matches.append(new_match)
                console.debug('MakeMatchesFromFile: Created {0}-{1}'.format(
                    new_match.racer_1.matchroom_name, new_match.racer_2.matchroom_name)
                )

            for racer_pair in desired_match_pairs:
                await make_single_match(racer_pair)
                await asyncio.sleep(0)

            matches = sorted(matches, key=lambda m: m.matchroom_name)

            await status_message.edit(
                content='Creating matches from file `{0}`... (Creating race rooms)'.format(filename)
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
            content='Creating matches from file `{0}`... done. {1}'.format(filename, report_str)
        )


class NextRace(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'next', 'nextrace', 'nextmatch')
        self.help_text = '`{0}` shows all upcoming matches; `{0} league_tag` shows only those upcoming matches for ' \
                         'the given league.'.format(self.mention)

    @property
    def short_help_text(self):
        return 'Show upcoming matches.'

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) > 1:
            await cmd.channel.send(
                'Too many arguments for `{0}`.'.format(self.mention)
            )
            return

        league_tag = None
        if len(cmd.args) == 1:
            league_tag = cmd.args[0].lower()
            try:
                await LeagueMgr().get_league(league_tag)
            except necrobot.exception.LeagueDoesNotExist:
                await cmd.channel.send(
                    'The league `{0}` does not exist.'.format(league_tag)
                )
                return

        utcnow = pytz.utc.localize(datetime.datetime.utcnow() - datetime.timedelta(minutes=1))
        num_to_show = 3

        matches = await leagueutil.get_upcoming_and_current(league_tag=league_tag)
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
            await leagueutil.get_nextrace_displaytext(upcoming_matches)
        )


class Register(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'register')
        self.help_text = 'Register for the current event.'

    async def _do_execute(self, cmd: Command):
        user = await userlib.get_user(discord_id=int(cmd.author.id))
        await leaguedb.register_user(user.user_id)


class SetLeagueName(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'set-league-name')
        self.help_text = '`{0} league_tag "league_name"`: Set the name of the given league.'.format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Change a league\'s name.'

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 2:
            await cmd.channel.send(
                'Error: Wrong number of arguments for `{0}`.'.format(self.mention)
            )
            return

        league_tag = cmd.args[0].lower()
        try:
            league = await LeagueMgr().get_league(league_tag)
        except necrobot.exception.LeagueDoesNotExist:
            await cmd.channel.send(
                'Error: League with tag `{0}` does not exist.'.format(league_tag)
            )
            return

        league.name = cmd.args[1]
        league.commit()
        await cmd.channel.send(
            'Set name of league `{0}` to "{1}".'.format(league_tag, league.name)
        )


class SetMatchRules(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'setrules')
        self.help_text = \
            '`{0} tag flags`: Set the tagged league\'s default match rules. Flags:\n' \
            '`bestof X | repeat X`: Set the match to be a best-of-X or a repeat-X.\n' \
            '`charname`: Set the default match character.\n' \
            '`u | s | seed X`: Set the races to be unseeded, seeded, or with a fixed seed.\n' \
            '`custom desc`: Give the matches a custom description.\n' \
            '`nodlc`: Matches are marked as being without the Amplified DLC.'.format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Set tagged league\'s default match rules.'

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) < 1:
            await cmd.channel.send(
                'Error: No arguments given!'
            )
            return

        league_tag = cmd.args[0].lower()
        try:
            league = await LeagueMgr().get_league(league_tag)
        except necrobot.exception.LeagueDoesNotExist:
            await cmd.channel.send(
                'Error: League `{}` does not exist.'.format(league_tag)
            )
            return

        try:
            match_info = matchinfo.parse_args(cmd.args[1:])
        except necrobot.exception.ParseException as e:
            await cmd.channel.send(
                'Error parsing inputs: {0}'.format(e)
            )
            return

        league.match_info = match_info
        league.commit()
        await cmd.channel.send(
            'Set the default match rules for `{0}` to {1}.'.format(league.tag, match_info.format_str)
        )


async def _do_cawmentary_command(cmd: Command, cmd_type: CommandType, add: bool):
    # Parse arguments
    try:
        match = await leagueutil.find_match(cmd.arg_string, finished_only=False)  # Only selects unfinished matches
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
