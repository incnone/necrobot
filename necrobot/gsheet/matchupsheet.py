import asyncio
import datetime
import unittest

import necrobot.exception
from necrobot.gsheet.makerequest import make_request
from necrobot.match import matchutil
from necrobot.user import userutil
from necrobot.util import console

from necrobot.gsheet.matchgsheetinfo import MatchGSheetInfo
from necrobot.gsheet.matchupsheetindexdata import MatchupSheetIndexData
from necrobot.gsheet.sheetcell import SheetCell
from necrobot.gsheet.sheetrange import SheetRange
from necrobot.gsheet.spreadsheets import Spreadsheets
from necrobot.match.match import Match
from necrobot.match.matchinfo import MatchInfo


class MatchupSheet(object):
    """
    Represents a single worksheet with matchup & scheduling data.
    """
    def __init__(self, gsheet_id: str):
        """
        Parameters
        ----------
        gsheet_id: str
            The ID of the GSheet on which this worksheet exists.
        """
        self.gsheet_id = gsheet_id
        self.column_data = MatchupSheetIndexData(gsheet_id=self.gsheet_id)

        self._not_found_matches = []

    @property
    def wks_name(self):
        return self.column_data.wks_name

    @property
    def wks_id(self):
        return self.column_data.wks_id

    def uncreated_matches(self):
        """All matches that failed to make from the most recent call to get_matches
        
        Returns
        -------
        list[str]
        """
        return self._not_found_matches

    async def initialize(self, wks_name: str = None, wks_id: int = None):
        await self.column_data.initalize(wks_name=wks_name, wks_id=wks_id)

    async def get_matches(self, **kwargs):
        """Read racer names and match types from the GSheet; create corresponding matches.
        
        Parameters
        ----------
        kwargs:
            Parameters to be passed to matchutil.make_match for every match made.
        
        Returns
        -------
        list[Match]
            The list of created Matches.
        """
        await self.column_data.refresh_footer()

        matches = []
        self._not_found_matches = []
        async with Spreadsheets() as spreadsheets:
            value_range = await self.column_data.get_values(spreadsheets)

            if 'values' not in value_range:
                return matches

            for row_idx, row_values in enumerate(value_range['values']):
                racer_1_name = row_values[self.column_data.racer_1].rstrip(' ')
                racer_2_name = row_values[self.column_data.racer_2].rstrip(' ')
                racer_1 = await userutil.get_user(any_name=racer_1_name, register=True)
                racer_2 = await userutil.get_user(any_name=racer_2_name, register=True)
                if racer_1 is None or racer_2 is None:
                    console.warning('Couldn\'t find racers for match {0}-{1}.'.format(
                        racer_1_name, racer_2_name
                    ))
                    self._not_found_matches.append('{0}-{1}'.format(racer_1_name, racer_2_name))
                    continue

                sheet_info = MatchGSheetInfo()
                sheet_info.wks_id = self.wks_id
                sheet_info.row = row_idx

                new_match = await matchutil.make_match(
                    racer_1_id=racer_1.user_id,
                    racer_2_id=racer_2.user_id,
                    gsheet_info=sheet_info,
                    **kwargs
                )
                matches.append(new_match)
        return matches

    async def schedule_match(self, match: Match):
        """Write scheduling data for the match into the GSheet.
        
        Parameters
        ----------
        match: Match

        """
        row = await self._get_match_row(match)
        if row is None:
            return

        if match.suggested_time is None:
            value = ''
        else:
            value = match.suggested_time.strftime('%Y-%m-%d %H:%M:%S')

        await self._update_cell(
            row=row,
            col=self.column_data.date,
            value=value,
            raw_input=False
        )

    async def set_vod(self, match: Match, vod_link: str):
        """Add a vod link to the GSheet.
        
        Parameters
        ----------
        match: Match
            The match to add a link for.
        vod_link: str
            The full URL of the VOD.
        """
        row = await self._get_match_row(match)
        if row is None:
            return
        if self.column_data.vod is None:
            console.warning('No Vod column on GSheet.')
            return

        await self._update_cell(
            row=row,
            col=self.column_data.vod,
            value=vod_link,
            raw_input=False
        )

    async def set_cawmentary(self, match: Match):
        """Add a cawmentator to the GSheet.
        
        Parameters
        ----------
        match: Match
            The match to add cawmentary for.
        """
        row = await self._get_match_row(match)
        if row is None:
            return
        if self.column_data.cawmentary is None:
            console.warning('No Cawmentary column on GSheet.')
            return

        cawmentator = await userutil.get_user(user_id=match.cawmentator_id)

        await self._update_cell(
            row=row,
            col=self.column_data.cawmentary,
            value=cawmentator.twitch_name if cawmentator is not None else '',
            raw_input=False
        )

    async def record_score(self, match: Match, winner: str, winner_wins: int, loser_wins: int):
        """Record the winner and final score of the match.
        
        Parameters
        ----------
        match: Match
        winner: str
        winner_wins: int
        loser_wins: int
        """
        row = await self._get_match_row(match)
        if row is None:
            return
        if self.column_data.winner is None:
            console.warning('No "Winner" column on GSheet.')
            return
        if self.column_data.score is None:
            console.warning('No "Score" column on GSheet.')
            return
        if self.column_data.score != self.column_data.winner + 1:
            console.warning("Can't record score; algorithm assumes the score column is one right of the winner column.")
            return

        sheet_range = SheetRange(
            ul_cell=(row, self.column_data.winner,),
            lr_cell=(row, self.column_data.score,),
            wks_name=self.wks_name
        )
        await self._update_cells(
            sheet_range=sheet_range,
            values=[[winner, '{0}-{1}'.format(winner_wins, loser_wins)]],
            raw_input=False
        )

    async def _get_match_row(self, match: Match) -> int or None:
        """Get the index of the row containing the Match.
        
        Parameters
        ----------
        match: Match

        Returns
        -------
        Optional[int]
            The row index (from 0) of the Match, or None if nothing found.
            
        Raises
        ------
        IncorrectWksException
            If the sheetID for this sheet doesn't match the match's sheetID
        """
        if match.sheet_id is not None and match.sheet_id != self.wks_id:
            raise necrobot.exception.IncorrectWksException(
                'Trying to find match {matchname}, but using incorrect MatchupSheet object '
                '(sheetID: {sheetid}, name: {sheetname})'.format(
                    matchname=match.matchroom_name,
                    sheetid=self.wks_id,
                    sheetname=self.wks_name
                )
            )

        if match.sheet_id is not None and match.sheet_row is not None:
            return match.sheet_row

        async with Spreadsheets() as spreadsheets:
            value_range = await self.column_data.get_values(spreadsheets)
            if 'values' not in value_range:
                return None

            match_regex_1 = match.racer_1.name_regex
            match_regex_2 = match.racer_2.name_regex

            values = value_range['values']
            for row, row_values in enumerate(values):
                gsheet_name_1 = row_values[self.column_data.racer_1]
                gsheet_name_2 = row_values[self.column_data.racer_2]
                if (match_regex_1.match(gsheet_name_1) and match_regex_2.match(gsheet_name_2)) \
                        or (match_regex_1.match(gsheet_name_2) and match_regex_2.match(gsheet_name_1)):
                    return row
            console.warning('Couldn\'t find match {0}-{1} on the GSheet.'.format(
                match.racer_1.rtmp_name,
                match.racer_2.rtmp_name
            ))
            return None

    async def _update_cell(self, row: int, col: int, value: str, raw_input: bool = True) -> bool:
        """Update a single cell.
        
        Parameters
        ----------
        row: int
            The row index (begins at 0).
        col: int
            The column index (begins at 0).
        value: str
            The cell value.
        raw_input: bool
            If False, GSheets will auto-format the input.

        Returns
        -------
        bool
            True if the update was successful.
        """
        if not self.column_data.valid:
            raise RuntimeError('Trying to update a cell on an invalid MatchupSheet.')

        row += self.column_data.header_row + 1
        col += self.column_data.min_column
        range_str = str(SheetCell(row, col, wks_name=self.wks_name))
        value_input_option = 'RAW' if raw_input else 'USER_ENTERED'
        value_range_body = {'values': [[value]]}
        async with Spreadsheets() as spreadsheets:
            request = spreadsheets.values().update(
                spreadsheetId=self.gsheet_id,
                range=range_str,
                valueInputOption=value_input_option,
                body=value_range_body
            )
            response = await make_request(request)
            return response is not None

    async def _update_cells(self, sheet_range: SheetRange, values: list, raw_input=True) -> bool:
        """Update all cells in a range.
        
        Parameters
        ----------
        sheet_range: SheetRange
            The range to update.
        values: list[list[str]]
            An array of values; one of the inner lists is a row, so values[i][j] is the ith row, jth column value.
        raw_input
            If False, GSheets will auto-format the input.
            
        Returns
        -------
        bool
            True if the update was successful.
        """
        if not self.column_data.valid:
            raise RuntimeError('Trying to update cells on an invalid MatchupSheet.')

        sheet_range = sheet_range.get_offset_by(self.column_data.header_row + 1, self.column_data.min_column)
        range_str = str(sheet_range)
        value_input_option = 'RAW' if raw_input else 'USER_ENTERED'
        value_range_body = {'values': values}
        async with Spreadsheets() as spreadsheets:
            request = spreadsheets.values().update(
                spreadsheetId=self.gsheet_id,
                range=range_str,
                valueInputOption=value_input_option,
                body=value_range_body
            )
            response = await make_request(request)
            return response is not None


class TestMatchupSheet(unittest.TestCase):
    from necrobot.test.asynctest import async_test

    loop = asyncio.new_event_loop()
    the_gsheet_id = '1JbwqUsX1ibHVVtcRVpOmaFJcfQz2ncBAOwb1nV1PsPA'

    @classmethod
    def setUpClass(cls):
        pass
        cls.sheet_1 = MatchupSheet(gsheet_id=TestMatchupSheet.the_gsheet_id)
        cls.sheet_2 = MatchupSheet(gsheet_id=TestMatchupSheet.the_gsheet_id)

        cls.loop.run_until_complete(cls.sheet_1.initialize(wks_name='Sheet1'))
        cls.loop.run_until_complete(cls.sheet_2.initialize(wks_name='Sheet2'))

        cls.match_1 = TestMatchupSheet.loop.run_until.complete(
            cls._get_match(
                r1_name='yjalexis',
                r2_name='macnd',
                time=datetime.datetime(year=2069, month=4, day=20, hour=4, minute=20),
                cawmentator_name='incnone'
            )
        )
        cls.match_2 = TestMatchupSheet.loop.run_until.complete(
            cls._get_match(
                r1_name='elad',
                r2_name='wilarseny',
                time=None,
                cawmentator_name=None
            )
        )

    @classmethod
    def tearDownClass(cls):
        cls.loop.close()

    @async_test(loop)
    def test_init(self):
        col_data = self.sheet_1.column_data
        self.assertEqual(col_data.tier, 1)
        self.assertEqual(col_data.racer_1, 2)
        self.assertEqual(col_data.racer_2, 3)
        self.assertEqual(col_data.date, 4)
        self.assertEqual(col_data.cawmentary, 5)
        self.assertEqual(col_data.winner, 6)
        self.assertEqual(col_data.score, 7)
        self.assertEqual(col_data.vod, 10)
        self.assertEqual(col_data.header_row, 3)
        self.assertEqual(col_data.footer_row, 8)

        bad_col_data = self.sheet_2.column_data
        self.assertIsNone(bad_col_data.header_row)

    @async_test(loop)
    def test_get_matches(self):
        matches = yield from self.sheet_1.get_matches()
        # noinspection PyTypeChecker
        self.assertEqual(len(matches), 4)
        match = matches[0]
        self.assertEqual(match.racer_1.rtmp_name, 'yjalexis')
        self.assertEqual(match.racer_2.rtmp_name, 'macnd')

    @async_test(loop)
    def test_schedule(self):
        try:
            yield from self.sheet_2._update_cell(row=4, col=4, value='Test update')
            self.assertTrue(False)
        except RuntimeError:
            pass
        yield from self.sheet_1.schedule_match(self.match_1)
        yield from self.sheet_1.schedule_match(self.match_2)

    @async_test(loop)
    def test_record_score(self):
        yield from self.sheet_1.record_score(self.match_1, 'macnd', 2, 1)
        yield from self.sheet_1.record_score(self.match_2, 'elad', 3, 1)

    @async_test(loop)
    def test_update_cawmentary_and_vod(self):
        yield from self.sheet_1.set_cawmentary(self.match_1)
        yield from self.sheet_1.set_vod(self.match_1, 'http://www.youtube.com/')

    @staticmethod
    async def _get_match(
            r1_name: str,
            r2_name: str,
            time: datetime.datetime or None,
            cawmentator_name: str or None
            ) -> Match:
        racer_1 = await userutil.get_user(any_name=r1_name, register=False)
        racer_2 = await userutil.get_user(any_name=r2_name, register=False)
        cawmentator = await userutil.get_user(rtmp_name=cawmentator_name)
        cawmentator_id = cawmentator.discord_id if cawmentator is not None else None

        match_info = MatchInfo(ranked=True)
        return await matchutil.make_match(
            racer_1_id=racer_1.user_id,
            racer_2_id=racer_2.user_id,
            match_info=match_info,
            suggested_time=time,
            cawmentator_id=cawmentator_id,
            register=False
        )
