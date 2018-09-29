import asyncio
import datetime
import typing
import unittest

from match.matchgsheetinfo import MatchGSheetInfo
from necrobot.gsheet.makerequest import make_request
from necrobot.gsheet.spreadsheets import Spreadsheets
from necrobot.gsheet.worksheetindexdata import WorksheetIndexData
from necrobot.match import matchdb, matchutil
from necrobot.match.match import Match
from necrobot.match.matchinfo import MatchInfo
from necrobot.user import userlib
from necrobot.util import console


class StandingsSheetIndexData(WorksheetIndexData):
    def __init__(self, gsheet_id: str):
        WorksheetIndexData.__init__(
            self,
            gsheet_id=gsheet_id,
            columns=list()
        )


class StandingsSheet(object):
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
        self.column_data = StandingsSheetIndexData(gsheet_id=self.gsheet_id)

        self._not_found_matches = []
        self._offset = None

    @property
    def wks_name(self) -> str:
        return self.column_data.wks_name

    @property
    def wks_id(self) -> str:
        return self.column_data.wks_id

    async def initialize(self, wks_name: str = None, wks_id: str = None) -> None:
        colnames = list()
        async with Spreadsheets() as spreadsheets:
            # Get names of other spreadsheets
            request = spreadsheets.get(spreadsheetId=self.gsheet_id)
            sheet_data = await make_request(request)
            for sheet in sheet_data['sheets']:
                props = sheet['properties']
                if (wks_name is not None and props['title'] != wks_name) \
                        or (wks_id is not None and props['sheetId'] != str(wks_id)):
                    colnames.append(props['title'])

            colnames.extend(['racer', 'results'])

        self.column_data.reset(columns=colnames)
        await self.column_data.initialize(wks_name=wks_name, wks_id=wks_id)
        min_col = None
        for colname in colnames:
            if colname == 'racer' or colname == 'results':
                continue
            if self.column_data.getcol(colname) is not None:
                min_col = min(min_col, self.column_data.getcol(colname)) if min_col is not None \
                    else self.column_data.getcol(colname)

        self._offset = min_col - self.column_data.results

    async def update_standings(self, match: Match, r1_wins: int, r2_wins: int) -> None:
        row_1, col_1, row_2, col_2 = await self._get_match_cells(match)
        if row_1 is not None and col_1 is not None:
            await self.column_data.update_cell(row_1, col_1 - self._offset, str(r1_wins), raw_input=False)
        if row_2 is not None and col_2 is not None:
            await self.column_data.update_cell(row_2, col_2 - self._offset, str(r2_wins), raw_input=False)

    async def _get_match_cells(self, match: Match) \
            -> typing.Tuple[typing.Optional[int], typing.Optional[int], typing.Optional[int], typing.Optional[int]]:
        """Get the cells to update for standings for the match.
        
        Parameters
        ----------
        match: Match

        Returns
        -------
        Tuple[int, int, int, int]
            The first pair is the (row, col) of racer 1's standings row, match against racer 2, and the second pair
            vice versa.
        """
        if match.sheet_id is None:
            console.warning(
                'Trying to update standings for match {0} fails because this match has no sheetID.'.format(
                    match.matchroom_name
                )
            )
            return None, None, None, None

        match_dupe_number = await matchdb.get_match_gsheet_duplication_number(match)
        async with Spreadsheets() as spreadsheets:
            # Get the column name for this match
            colname = None
            request = spreadsheets.get(spreadsheetId=self.gsheet_id)
            sheet_data = await make_request(request)
            for sheet in sheet_data['sheets']:
                props = sheet['properties']
                if match.sheet_id == props['sheetId']:
                    colname = props['title']

            if colname is None:
                console.warning(
                    'Trying to get cells for match {0} fails because the sheet corresponding to its sheetID '
                    'could not be found.'.format(match.matchroom_name)
                )
                return None, None, None, None
            if self.column_data.getcol(colname) is None:
                console.warning(
                    'Trying to get cells for match {0} fails because the column corresponding to its worksheet '
                    '("{1}") could not be found.'.format(match.matchroom_name, colname)
                )
                return None, None, None, None

            value_range = await self.column_data.get_values(spreadsheets, extend_right=True)
            if 'values' not in value_range:
                return None, None, None, None

            r1_row = None
            r2_row = None
            r1_col = None
            r2_col = None
            values = value_range['values']

            for row, row_values in enumerate(values):
                gsheet_name = row_values[self.column_data.racer]
                if match.racer_1.name_regex.match(gsheet_name):
                    r1_row = row
                    match_dupe_1 = match_dupe_number
                    for col in range(self.column_data.getcol(colname), len(row_values)):
                        if match.racer_2.name_regex.match(row_values[col]):
                            match_dupe_1 -= 1
                            if match_dupe_1 < 0:
                                r1_col = col
                                break
                elif match.racer_2.name_regex.match(gsheet_name):
                    r2_row = row
                    match_dupe_2 = match_dupe_number
                    for col in range(self.column_data.getcol(colname), len(row_values)):
                        if match.racer_1.name_regex.match(row_values[col]):
                            match_dupe_2 -= 1
                            if match_dupe_2 < 0:
                                r2_col = col
                                break

            return r1_row, r1_col, r2_row, r2_col


class TestStandingsSheet(unittest.TestCase):
    from necrobot.test.asynctest import async_test
    from match.matchgsheetinfo import MatchGSheetInfo

    loop = asyncio.new_event_loop()
    the_gsheet_id = '1JbwqUsX1ibHVVtcRVpOmaFJcfQz2ncBAOwb1nV1PsPA'

    @classmethod
    def setUpClass(cls):
        pass
        cls.sheet = StandingsSheet(gsheet_id=TestStandingsSheet.the_gsheet_id)

        cls.loop.run_until_complete(cls.sheet.initialize(wks_name='Standings'))

        match_1_sheetinfo = MatchGSheetInfo(wks_id=0, row=0)
        match_2_sheetinfo = MatchGSheetInfo(wks_id=0, row=1)

        cls.match_1 = TestStandingsSheet.loop.run_until_complete(
            cls._get_match(
                r1_name='yjalexis',
                r2_name='macnd',
                time=datetime.datetime(year=2069, month=4, day=20, hour=4, minute=20),
                cawmentator_name='incnone',
                gsheet_info=match_1_sheetinfo
            )
        )
        cls.match_2 = TestStandingsSheet.loop.run_until_complete(
            cls._get_match(
                r1_name='elad',
                r2_name='wilarseny',
                time=None,
                cawmentator_name=None,
                gsheet_info=match_2_sheetinfo
            )
        )

    @classmethod
    def tearDownClass(cls):
        cls.loop.close()

    @async_test(loop)
    def test_init(self):
        col_data = self.sheet.column_data
        self.assertEqual(col_data.racer, 0)
        self.assertEqual(col_data.results, 2)
        self.assertEqual(col_data.Sheet1, 4)
        self.assertEqual(self.sheet._offset, 2)

    @async_test(loop)
    def test_record(self):
        yield from self.sheet.update_standings(self.match_1, 2, 1)
        yield from self.sheet.update_standings(self.match_2, 0, 3)

    @staticmethod
    async def _get_match(
            r1_name: str,
            r2_name: str,
            time: datetime.datetime or None,
            cawmentator_name: str or None,
            gsheet_info: MatchGSheetInfo
            ) -> Match:
        racer_1 = await userlib.get_user(any_name=r1_name, register=False)
        racer_2 = await userlib.get_user(any_name=r2_name, register=False)
        cawmentator = await userlib.get_user(rtmp_name=cawmentator_name)
        cawmentator_id = cawmentator.discord_id if cawmentator is not None else None

        match_info = MatchInfo(ranked=True)
        return await matchutil.make_match(
            racer_1_id=racer_1.user_id,
            racer_2_id=racer_2.user_id,
            match_info=match_info,
            suggested_time=time,
            cawmentator_id=cawmentator_id,
            register=False,
            gsheet_info=gsheet_info
        )
