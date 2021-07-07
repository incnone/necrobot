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
from necrobot.condorbot.condormgr import CondorMgr


class GetGSheet(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'gsheet', 'getgsheet')
        self.help_text = '`{0} league_tag`: Return a link to to the league\'s gsheet.'
        self.admin_only = True

    @property
    def short_help_text(self):
        return 'Current GSheet info.'

    async def _do_execute(self, cmd: Command):
        if not len(cmd.args) == 1:
            await cmd.channel.send(
                'Wrong number of arguments for `{}`.'.format(self.mention)
            )
            return

        gsheet_id = CondorMgr().event.gsheet_id
        if gsheet_id is None:
            await cmd.channel.send(
                'Error: GSheet for this league is not yet set. Use `.setgsheet`.'
            )
            return

        try:
            perm_info = await sheetutil.has_read_write_permissions(gsheet_id)
        except googleapiclient.errors.Error as e:
            await cmd.channel.send(
                'Error: {0}'.format(e)
            )
            return

        if not perm_info[0]:
            await cmd.channel.send(
                'Cannot access GSheet: {0}'.format(perm_info[1])
            )
            return

        league_tag = cmd.args[0].lower()
        try:
            league = await LeagueMgr().get_league(league_tag)
        except necrobot.exception.LeagueDoesNotExist:
            await cmd.channel.send(
                'Error: The league with tag `{0}` does not exist.'.format(league_tag)
            )
            return

        if league.worksheet_id is None:
            await cmd.channel.send(
                'The league `{0}` does not have a worksheet set. Use `.set-league-worksheet`.'.format(league_tag)
            )
            return

        await cmd.channel.send(
            'The GSheet for `{league_name}` is "{sheet_name}". '
            '<https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={wks_id}>'
            .format(
                league_name=league.tag,
                sheet_name=perm_info[1],
                sheet_id=gsheet_id,
                wks_id=league.worksheet_id
            )
        )


# class MakeFromSheet(CommandType):
#     def __init__(self, bot_channel):
#         CommandType.__init__(self, bot_channel, 'makematches', 'makefromsheet', 'makeweek')
#         self.help_text = '`{0} league_tag sheetname`: make races from the worksheet `sheetname`. (Note that the ' \
#                          'bot must be pointed at the correct GSheet for this to work; this can be set via the ' \
#                          'bot\'s config file, or by calling `.setgsheet`.'.format(self.mention)
#         self.admin_only = True
#
#     @property
#     def short_help_text(self):
#         return 'Make match rooms.'
#
#     async def _do_execute(self, cmd: Command):
#         if len(cmd.args) != 2:
#             await cmd.channel.send(
#                 'Wrong number of arguments for `{0}`.'.format(self.mention)
#             )
#             return
#
#         league_tag = cmd.args[0]
#         try:
#             league = await LeagueMgr().get_league(league_tag)
#         except necrobot.exception.LeagueDoesNotExist:
#             await cmd.channel.send(
#                 'Error: The league with tag `{0}` does not exist.'.format(league_tag)
#             )
#             return
#
#         wks_name = cmd.args[1]
#         status_message = await cmd.channel.send(
#             'Creating matches from worksheet `{0}`... (Getting GSheet info)'.format(wks_name)
#         )
#
#         async with cmd.channel.typing():
#             match_info = league.match_info
#
#             console.info('MakeFromSheet: Getting GSheet info...')
#             try:
#                 matchup_sheet = await sheetlib.get_sheet(
#                         gsheet_id=league.gsheet_id,
#                         wks_name=wks_name,
#                         sheet_type=sheetlib.SheetType.MATCHUP
#                     )  # type: MatchupSheet
#                 matches = await matchup_sheet.get_matches(register=True, match_info=match_info)
#             except (googleapiclient.errors.Error, necrobot.exception.NecroException) as e:
#                 await cmd.channel.send(
#                     'Error while making matchups: `{0}`'.format(e)
#                 )
#                 return
#
#             console.info('MakeFromSheet: Creating Match objects...')
#             await status_message.edit(
#                 content='Creating matches from worksheet `{0}`... (Creating match list)'.format(wks_name)
#             )
#             not_found_matches = matchup_sheet.uncreated_matches()
#             matches_with_channels = await matchchannelutil.get_matches_with_channels()
#
#             console.info('MakeFromSheet: Removing duplicate matches...')
#             # Remove matches from the list that already have channels
#             unchanneled_matches = []
#             for match in matches:
#                 found = False
#                 for channeled_match in matches_with_channels:
#                     if match.match_id == channeled_match.match_id:
#                         found = True
#                 if not found:
#                     unchanneled_matches.append(match)
#
#             console.info('MakeFromSheet: Sorting matches...')
#             # Sort the remaining matches
#             unchanneled_matches = sorted(unchanneled_matches, key=lambda m: m.matchroom_name)
#
#             await status_message.edit(
#                 content='Creating matches from worksheet `{0}`... (Creating race rooms)'.format(wks_name)
#             )
#             console.debug('MakeFromSheet: Matches to make: {0}'.format(unchanneled_matches))
#             console.info('MakeFromSheet: Creating match channels...')
#             for match in unchanneled_matches:
#                 console.info('MakeFromSheet: Creating {0}...'.format(match.matchroom_name))
#                 new_room = await matchchannelutil.make_match_room(match=match, register=False)
#                 await new_room.send_channel_start_text()
#
#             uncreated_str = ''
#             for match_str in not_found_matches:
#                 uncreated_str += match_str + ', '
#             if uncreated_str:
#                 uncreated_str = uncreated_str[:-2]
#
#             if uncreated_str:
#                 report_str = 'The following matches were not made: {0}'.format(uncreated_str)
#             else:
#                 report_str = 'All matches created successfully.'
#
#         await status_message.edit(
#             content='Creating matches from worksheet `{0}`... done. {1}'.format(wks_name, report_str)
#         )


# class PushMatchToSheet(CommandType):
#     def __init__(self, bot_channel):
#         CommandType.__init__(self, bot_channel, 'updategsheet')
#         self.help_text = 'Update the match\'s info on the GSheet.'
#         self.admin_only = True
#
#     async def _do_execute(self, cmd: Command):
#         match = self.bot_channel.match      # type: Match
#         wks_id = match.sheet_id
#         if wks_id is None:
#             await cmd.channel.send(
#                 'Error: No worksheet is assigned to this match (contact incnone).'
#             )
#             return
#
#         match_row = match.sheet_row
#         if match_row is None:
#             await cmd.channel.send(
#                 'Error: This match doesn\'t have a designated sheet row (contact incnone).'
#             )
#             return
#
#         league_tag = match.league_tag
#         if league_tag is None:
#             await cmd.channel.send(
#                 'Error: This match is not attached to a league.'
#             )
#             return
#
#         try:
#             league = await LeagueMgr().get_league(league_tag)
#         except necrobot.exception.LeagueDoesNotExist:
#             await cmd.channel.send(
#                 'Error: This match is attached to league `{}`, but that league cannot be found.'.format(league_tag)
#             )
#             return
#
#         try:
#             matchup_sheet = await sheetlib.get_sheet(
#                     gsheet_id=league.gsheet_id,
#                     wks_id=wks_id,
#                     sheet_type=sheetlib.SheetType.MATCHUP
#                 )  # type: MatchupSheet
#             standings_sheet = await sheetlib.get_sheet(
#                     gsheet_id=league.gsheet_id,
#                     wks_name='Standings',
#                     sheet_type=sheetlib.SheetType.STANDINGS
#                 )  # type: StandingsSheet
#         except (googleapiclient.errors.Error, necrobot.exception.NecroException) as e:
#             await cmd.channel.send(
#                 'Error accessing GSheet: `{0}`'.format(e)
#             )
#             return
#
#         # TODO after combining MatchRaceData with match, simplify (code duping with MatchRoom)
#         if match.is_scheduled:
#             await matchup_sheet.schedule_match(match)
#         await matchup_sheet.set_cawmentary(match)
#         match_race_data = await matchutil.get_race_data(match)    # type: MatchRaceData
#
#         if match.is_best_of:
#             played_all = match_race_data.leader_wins > match.number_of_races // 2
#         else:
#             played_all = match_race_data.num_finished >= match.number_of_races
#
#         if played_all:
#             # Send event
#             if match_race_data.r1_wins > match_race_data.r2_wins:
#                 winner = match.racer_1.gsheet_name
#                 winner_wins = match_race_data.r1_wins
#                 loser_wins = match_race_data.r2_wins
#             elif match_race_data.r2_wins > match_race_data.r1_wins:
#                 winner = match.racer_2.gsheet_name
#                 winner_wins = match_race_data.r2_wins
#                 loser_wins = match_race_data.r1_wins
#             else:
#                 winner = '[Tied]'
#                 winner_wins = match_race_data.r1_wins
#                 loser_wins = match_race_data.r2_wins
#
#             await matchup_sheet.record_score(
#                 match=match, winner=winner, winner_wins=winner_wins, loser_wins=loser_wins
#             )
#             await standings_sheet.update_standings(
#                 match=match,
#                 r1_wins=match_race_data.r1_wins,
#                 r2_wins=match_race_data.r2_wins
#             )
#
#         await cmd.channel.send(
#             'Sheet updated.'
#         )


class SetLeagueWorksheet(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'set-league-worksheet')
        self.help_text = '`{0} league_tag worksheet_id` : Set the bot to use the GSheet with the given ID for the ' \
                         'given league. Note: the worksheet_id of a GSheet is the short sequence of numbers after ' \
                         '`gid=` in its URL. (The URL looks like ' \
                         'docs.google.com/spreadsheets/d/`sheet_id`/edit#gid=`worksheet_id`; ' \
                         'you want `worksheet_id`.) Note that the bot must have read-write access to the GSheet.' \
                         .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return "Set the league's worksheet."

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 2:
            await cmd.channel.send(
                'Wrong number of arguments for `{0}`.'.format(self.mention)
            )
            return

        sheet_id = CondorMgr().event.gsheet_id
        if sheet_id is None:
            await cmd.channel.send(
                'Error: The current event does not have a GSheet set; you must set a GSheet (`.set-event-gsheet`) '
                'before calling `{}`.'.format(self.mention)
            )
            return

        perm_info = await sheetutil.has_read_write_permissions(sheet_id)

        if not perm_info[0]:
            await cmd.channel.send(
                'Cannot access GSheet: {0}'.format(perm_info[1])
            )
            return

        league_tag = cmd.args[0].lower()
        try:
            league = await LeagueMgr().get_league(league_tag)
        except necrobot.exception.LeagueDoesNotExist:
            await cmd.channel.send(
                'Error: The league with tag `{0}` does not exist.'.format(league_tag)
            )
            return

        worksheet_id = cmd.args[1]
        league.worksheet_id = worksheet_id
        league.commit()
        await cmd.channel.send(
            'Set the worksheet for `{league}` to <https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={wks_id}>'
            .format(
                league=league_tag,
                sheet_id=sheet_id,
                wks_id=worksheet_id
            )
        )


class SetEventGSheet(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'set-event-gsheet')
        self.help_text = '`{0} gsheet_id` : Set the bot to use the GSheet for the current event.' \
                         'Note: the gsheet_id of a GSheet is the long sequence of letters and numbers in its URL. ' \
                         '(The URL looks like docs.google.com/spreadsheets/d/`sheet_id`/edit#gid=`worksheet_id`; ' \
                         'you want `sheet_id`.) Note that the bot must have read-write access to the GSheet.' \
                         .format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return "Set the event's gsheet."

    async def _do_execute(self, cmd: Command):
        if len(cmd.args) != 1:
            await cmd.channel.send(
                'Wrong number of arguments for `{0}`.'.format(self.mention)
            )
            return

        sheet_id = cmd.args[0]
        perm_info = await sheetutil.has_read_write_permissions(sheet_id)

        if not perm_info[0]:
            await cmd.channel.send(
                'Cannot access GSheet: {0}'.format(perm_info[1])
            )
            return

        await CondorMgr().set_gsheet_id(sheet_id)
        await cmd.channel.send(
            'Set event\'s GSheet to "{name}". <https://docs.google.com/spreadsheets/d/{sheet_id}>'.format(
                name=perm_info[1],
                sheet_id=sheet_id
            )
        )


class OverwriteGSheet(CommandType):
    def __init__(self, bot_channel):
        CommandType.__init__(self, bot_channel, 'overwritegsheet')
        self.help_text = "`{} league_tag`: Refresh the GSheet (overwrites all data).".format(self.mention)
        self.admin_only = True

    @property
    def short_help_text(self):
        return "Refresh a league's GSheet."

    async def _do_execute(self, cmd: Command):
        gsheet_id = CondorMgr().event.gsheet_id
        if gsheet_id is None:
            await cmd.channel.send(
                'Error: GSheet for this league is not yet set. Use `.setgsheet`.'
            )
            return

        try:
            perm_info = await sheetutil.has_read_write_permissions(gsheet_id)
        except googleapiclient.errors.Error as e:
            await cmd.channel.send(
                'Error: {0}'.format(e)
            )
            return

        if not perm_info[0]:
            await cmd.channel.send(
                'Cannot access GSheet: {0}'.format(perm_info[1])
            )
            return

        # Get the matchup sheet
        league_tag = cmd.args[0].lower()
        try:
            league = await LeagueMgr().get_league(league_tag)
        except necrobot.exception.LeagueDoesNotExist:
            await cmd.channel.send(
                'Error: The league with tag `{0}` does not exist.'.format(league_tag)
            )
            return

        try:
            standings_sheet = await sheetlib.get_sheet(
                    gsheet_id=gsheet_id,
                    wks_id=league.worksheet_id,
                    sheet_type=sheetlib.SheetType.STANDINGS
                )  # type: StandingsSheet
        except (googleapiclient.errors.Error, necrobot.exception.NecroException) as e:
            await cmd.channel.send(
                'Error accessing GSheet: `{0}`'.format(e)
            )
            return

        if standings_sheet is None:
            await cmd.channel.send('Error: StandingsSheet is None.')
            return

        await standings_sheet.overwrite_gsheet(league_tag=league_tag)
        await cmd.channel.send('Sheet updated.')
