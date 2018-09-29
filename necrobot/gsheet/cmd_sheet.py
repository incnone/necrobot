import googleapiclient.errors

import necrobot.exception

from necrobot.util import console
from necrobot.gsheet import sheetlib
from necrobot.gsheet import sheetutil
from necrobot.match import matchutil
from necrobot.match import matchchannelutil

from necrobot.botbase.command import Command
from necrobot.botbase.commandtype import CommandType
from necrobot.match.match import Match
from necrobot.match.matchracedata import MatchRaceData
from necrobot.gsheet.matchupsheet import MatchupSheet
from necrobot.gsheet.standingssheet import StandingsSheet
from necrobot.league.leaguemgr import LeagueMgr


class GetGSheet(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'gsheet', 'getgsheet')
        self.help_text = 'Return the name of the current GSheet, and a link to it, if the bot has ' \
                         'permissions; otherwise, returns an error message.'
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Current GSheet info.'

    async def _do_execute(self, cmd: Command):
        await self.client.send_typing(cmd.channel)

        gsheet_id = LeagueMgr().league.gsheet_id
        if gsheet_id is None:
            await self.client.send_message(
                cmd.channel,
                'Error: GSheet for this league is not yet set. Use `.setgsheet`.'
            )
            return

        try:
            perm_info = await sheetutil.has_read_write_permissions(LeagueMgr().league.gsheet_id)
        except googleapiclient.errors.Error as e:
            await self.client.send_message(
                cmd.channel,
                'Error: {0}'.format(e)
            )
            return

        if not perm_info[0]:
            await self.client.send_message(
                cmd.channel,
                'Cannot access GSheet: {0}'.format(perm_info[1])
            )
            return
        else:
            await self.client.send_message(
                cmd.channel,
                'The GSheet for `{league_name}` is "{sheet_name}". <{sheet_url}>'.format(
                    league_name=LeagueMgr().league.schema_name,
                    sheet_name=perm_info[1],
                    sheet_url='https://docs.google.com/spreadsheets/d/{0}'.format(LeagueMgr().league.gsheet_id)
                )
            )


class MakeFromSheet(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'makematches', 'makefromsheet', 'makeweek')
        self.help_text = '`{0} sheetname`: make races from the worksheet `sheetname`. (Note that the ' \
                         'bot must be pointed at the correct GSheet for this to work; this can be set via the bot\'s ' \
                         'config file, or by calling `.setgsheet`.'.format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Make match rooms.'

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                'Wrong number of arguments for `{0}`.'.format(self.mention)
            )
            return

        wks_name = cmd.args[0]
        await self.client.send_message(
            cmd.channel,
            'Creating matches from worksheet `{0}`...'.format(wks_name)
        )
        await self.client.send_typing(cmd.channel)

        match_info = LeagueMgr().league.match_info

        console.info('MakeFromSheet: Getting GSheet info...')
        try:
            matchup_sheet = await sheetlib.get_sheet(
                    gsheet_id=LeagueMgr().league.gsheet_id,
                    wks_name=wks_name,
                    sheet_type=sheetlib.SheetType.MATCHUP
                )  # type: MatchupSheet
            matches = await matchup_sheet.get_matches(register=False, match_info=match_info)
        except (googleapiclient.errors.Error, necrobot.exception.NecroException) as e:
            await self.client.send_message(
                cmd.channel,
                'Error while making matchups: `{0}`'.format(e)
            )
            return

        console.info('MakeFromSheet: Creating Match objects...')
        not_found_matches = matchup_sheet.uncreated_matches()
        matches_with_channels = await matchchannelutil.get_matches_with_channels()
        channeled_matchroom_names = dict()
        for match in matches_with_channels:
            if match.matchroom_name in channeled_matchroom_names:
                channeled_matchroom_names[match.matchroom_name] += 1
            else:
                channeled_matchroom_names[match.matchroom_name] = 1

        console.info('MakeFromSheet: Removing duplicate matches...')
        # Remove matches that have the same name as current channels (but only one per channel)
        unchanneled_matches = []
        for match in matches:
            channeled_name = match.matchroom_name in channeled_matchroom_names
            if not channeled_name or channeled_matchroom_names[match.matchroom_name] <= 0:
                unchanneled_matches.append(match)
            if channeled_name:
                channeled_matchroom_names[match.matchroom_name] -= 1

        console.info('MakeFromSheet: Sorting matches...')
        # Sort the remaining matches
        unchanneled_matches = sorted(unchanneled_matches, key=lambda m: m.matchroom_name)

        console.debug('MakeFromSheet: Matches to make: {0}'.format(unchanneled_matches))
        console.info('MakeFromSheet: Creating match channels...')
        for match in unchanneled_matches:
            console.info('MakeFromSheet: Creating {0}...'.format(match.matchroom_name))
            new_room = await matchchannelutil.make_match_room(match=match, register=True)
            await new_room.send_channel_start_text()

        uncreated_str = ''
        for match_str in not_found_matches:
            uncreated_str += match_str + ', '
        if uncreated_str:
            uncreated_str = uncreated_str[:-2]

        if uncreated_str:
            report_str = 'Done creating matches. The following matches were not made: {0}'.format(uncreated_str)
        else:
            report_str = 'All matches created successfully.'

        await self.client.send_message(cmd.channel, report_str)


class PushMatchToSheet(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'updategsheet')
        self.help_text = 'Update the match\'s info on the GSheet.'
        self.admin_only = True

    async def _do_execute(self, cmd: Command):
        match = self.bot_channel.match      # type: Match
        wks_id = match.sheet_id
        if wks_id is None:
            await self.client.send_message(
                cmd.channel,
                'Error: No worksheet is assigned to this match (contact incnone).'
            )
            return

        match_row = match.sheet_row
        if match_row is None:
            await self.client.send_message(
                cmd.channel,
                'Error: This match doesn\'t have a designated sheet row (contact incnone).'
            )
            return

        try:
            matchup_sheet = await sheetlib.get_sheet(
                    gsheet_id=LeagueMgr().league.gsheet_id,
                    wks_id=wks_id,
                    sheet_type=sheetlib.SheetType.MATCHUP
                )  # type: MatchupSheet
            standings_sheet = await sheetlib.get_sheet(
                    gsheet_id=LeagueMgr().league.gsheet_id,
                    wks_name='Standings',
                    sheet_type=sheetlib.SheetType.STANDINGS
                )  # type: StandingsSheet
        except (googleapiclient.errors.Error, necrobot.exception.NecroException) as e:
            await self.client.send_message(
                cmd.channel,
                'Error accessing GSheet: `{0}`'.format(e)
            )
            return

        # TODO after combining MatchRaceData with match, simplify (code duping with MatchRoom)
        if match.is_scheduled:
            await matchup_sheet.schedule_match(match)
        await matchup_sheet.set_cawmentary(match)
        match_race_data = await matchutil.get_race_data(match)    # type: MatchRaceData

        if match.is_best_of:
            played_all = match_race_data.leader_wins > match.number_of_races // 2
        else:
            played_all = match_race_data.num_finished >= match.number_of_races

        if played_all:
            # Send event
            if match_race_data.r1_wins > match_race_data.r2_wins:
                winner = match.racer_1.gsheet_name
                winner_wins = match_race_data.r1_wins
                loser_wins = match_race_data.r2_wins
            elif match_race_data.r2_wins > match_race_data.r1_wins:
                winner = match.racer_2.gsheet_name
                winner_wins = match_race_data.r2_wins
                loser_wins = match_race_data.r1_wins
            else:
                winner = '[Tied]'
                winner_wins = match_race_data.r1_wins
                loser_wins = match_race_data.r2_wins

            await matchup_sheet.record_score(
                match=match, winner=winner, winner_wins=winner_wins, loser_wins=loser_wins
            )
            await standings_sheet.update_standings(
                match=match,
                r1_wins=match_race_data.r1_wins,
                r2_wins=match_race_data.r2_wins
            )

        await self.client.send_message(
            cmd.channel,
            'Sheet updated.'
        )


class SetGSheet(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'setgsheet')
        self.help_text = '`{0} sheet_id` : Set the bot to read from the GSheet with the given ID. This ' \
                         'will modify the bot\'s config file, and this sheet will become the default. Note: the ID ' \
                         'of a GSheet is the long sequence of letters and numbers in its URL. (The URL looks like ' \
                         'docs.google.com/spreadsheets/d/`sheet_id`/edit#gid=`worksheet_id`; you want `sheet_id`.) ' \
                         'Note that the bot must have read-write access to the GSheet.' \
                         .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return "Set the bot's GSheet."

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 1:
            await self.client.send_message(
                cmd.channel,
                'Wrong number of arguments for `{0}`.'.format(self.mention)
            )
            return

        sheet_id = cmd.args[0]
        perm_info = await sheetutil.has_read_write_permissions(sheet_id)

        if not perm_info[0]:
            await self.client.send_message(
                cmd.channel,
                'Cannot access GSheet: {0}'.format(perm_info[1])
            )
            return

        LeagueMgr().league.gsheet_id = sheet_id
        LeagueMgr().league.commit()
        await self.client.send_message(
            cmd.channel,
            'Set default GSheet to "{0}". <{1}>'.format(
                perm_info[1],
                'https://docs.google.com/spreadsheets/d/{0}'.format(sheet_id)
            )
        )
