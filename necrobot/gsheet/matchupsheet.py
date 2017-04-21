import unittest

from necrobot.gsheet.sheetutil import SheetCell, SheetRange
from necrobot.util import console
from necrobot.user import userutil

from necrobot.gsheet.spreadsheets import Spreadsheets
from necrobot.race.match import matchutil


class MatchupSheetIndexData(object):
    """
    Stores the index of various columns on a CoNDOR matchup sheet.
    Call init() to read these indicies automatically from searching the sheet.
    """

    def __init__(self, gsheet_id, wks_name=None):
        self.gsheet_id = gsheet_id
        self.wks_name = wks_name

        # Column indicies
        self._racer_1 = None
        self._racer_2 = None

        self._cawmentary = None
        self._date = None
        self._match_type = None
        self._score = None
        self._tier = None
        self._vod = None
        self._winner = None

        self.min_column = None
        self.max_column = None

        # Row indicies
        self.header_row = None
        self.footer_row = None

        # Call init
        self._init()

    def _init(self):
        with Spreadsheets() as spreadsheets:
            # Find the size of the worksheet
            sheet_size = None
            sheet_data = spreadsheets.get(spreadsheetId=self.gsheet_id).execute()
            for sheet in sheet_data['sheets']:
                props = sheet['properties']
                if props['title'] == self.wks_name:
                    sheet_size = (int(props['gridProperties']['rowCount']),
                                  int(props['gridProperties']['columnCount']),)
                    break

            if sheet_size is None:
                console.error(
                    'Couldn\'t find a worksheet. GSheetID: {0}, Worksheet Name: {1}.'.format(gsheet_id, self.wks_name))
                return

            # Find the header row and the column indicies
            row_query_min = 1
            row_query_max = 10
            col_vals = []
            while self.footer_row is None and row_query_min <= sheet_size[0]:
                # Get the cells
                range_to_get = SheetRange(
                    ul_cell=(row_query_min, 1,),
                    lr_cell=(row_query_max, sheet_size[1],),
                    wks_name=self.wks_name
                )
                value_range = spreadsheets.values().get(
                    spreadsheetId=self.gsheet_id,
                    range=range_to_get,
                    majorDimension='ROWS'
                ).execute()

                # Check if the cells we got are completely empty
                if 'values' not in value_range:
                    if self.header_row is not None:
                        self.footer_row = row_query_min

                # If there are values in the cells, find header and footers
                else:
                    values = value_range['values']
                    for row, row_values in enumerate(values):
                        row += 1
                        if self.header_row is None:
                            for col, cell_value in enumerate(row_values):
                                if self._make_index(cell_value, col + 1):
                                    self.header_row = row
                                    col_vals.append(col)

                    # If we got fewer than the requested number of rows, we've found the footer
                    if len(values) < row_query_max - row_query_min + 1:
                        self.footer_row = row_query_min + len(values)

                # Prepare for next loop
                row_query_min = row_query_max + 1
                row_query_max = min(2*row_query_max, sheet_size[0])

            if col_vals:
                self.min_column = min(self.min_column, min(col_vals)) if self.min_column is not None else min(col_vals)
                self.max_column = max(self.max_column, max(col_vals)) if self.max_column is not None else max(col_vals)

    @property
    def racer_1(self):
        return self._racer_1 - self.min_column

    @property
    def racer_2(self):
        return self._racer_2 - self.min_column

    @property
    def cawmentary(self):
        return self._cawmentary - self.min_column

    @property
    def date(self):
        return self._date - self.min_column

    @property
    def match_type(self):
        return self._match_type - self.min_column

    @property
    def score(self):
        return self._score - self.min_column

    @property
    def tier(self):
        return self._tier - self.min_column

    @property
    def vod(self):
        return self._vod - self.min_column

    @property
    def winner(self):
        return self._winner - self.min_column

    @property
    def full_range(self):
        return SheetRange(
            ul_cell=(self.header_row + 1, self.min_column,),
            lr_cell=(self.footer_row - 1, self.max_column,),
            wks_name=self.wks_name
        )

    def get_values(self, spreadsheets):
        range_to_get = self.full_range
        return spreadsheets.values().get(
            spreadsheetId=self.gsheet_id,
            range=range_to_get,
            majorDimension='ROWS'
        ).execute()

    def _make_index(self, cell_value: str, col: int) -> bool:
        cell_value = cell_value.lower()
        if cell_value.startswith('racer 1'):
            self._racer_1 = col
            return True
        elif cell_value.startswith('racer 2'):
            self._racer_2 = col
            return True
        elif cell_value.startswith('cawmentary'):
            self._cawmentary = col
            return True
        elif cell_value.startswith('date'):
            self._date = col
            return True
        elif 'score' in cell_value:
            self._score = col
            return True
        elif cell_value.startswith('tier'):
            self._tier = col
            return True
        elif 'type' in cell_value:
            self._match_type = col
            return True
        elif cell_value.startswith('vod'):
            self._vod = col
            return True
        elif cell_value.startswith('winner'):
            self._winner = col
            return True
        return False


class MatchupSheet(object):
    """
    Represents a single worksheet with matchup & scheduling data.
    """

    def __init__(self, gsheet_id, wks_name=None):
        self.gsheet_id = gsheet_id
        self.wks_name = wks_name
        self.column_data = MatchupSheetIndexData(self.gsheet_id, self.wks_name)

    def get_matches(self):
        """
        Reads racer names and match types from the GSheet and create corresponding Match objects.
        :return: A list of Match objects.
        """
        matches = []
        with Spreadsheets() as spreadsheets:
            value_range = self.column_data.get_values(spreadsheets)

            if 'values' not in value_range:
                return matches

            for row_values in value_range['values']:
                racer_1_name = row_values[self.column_data.racer_1]
                racer_2_name = row_values[self.column_data.racer_2]
                racer_1 = userutil.get_user(any_name=racer_1_name, register=True)
                racer_2 = userutil.get_user(any_name=racer_2_name, register=True)
                if racer_1 is None or racer_2 is None:
                    console.error('Couldn\'t find racers for match {0}-{1}.'.format(
                        racer_1_name, racer_2_name
                    ))
                    continue

                # type_str = row_values[self.column_data.match_type]  # TODO
                # tier = row_values[self.column_data.tier]  # TODO

                new_match = matchutil.make_registered_match(
                    racer_1_id=racer_1.user_id,
                    racer_2_id=racer_2.user_id,
                    ranked=True
                )
                matches.append(new_match)
        return matches

    def schedule_match(self, match):
        """
        Write scheduling data for a match into the GSheet.
        :param match: The Match object to schedule.
        """
        row = self._get_match_row(match)
        if row is None:
            return

    def _get_match_row(self, match) -> int or None:
        """
        Get the index for the row containing the match.
        :param match: The Match to find the row for.
        :return: The index of the Match, or None if nothing found.
        """
        with Spreadsheets() as spreadsheets:
            value_range = self.column_data.get_values(spreadsheets)
            if 'values' not in value_range:
                return None

            match_names = {match.racer_1.rtmp_name, match.racer_2.rtmp_name}

            values = value_range['values']
            for row, row_values in enumerate(values):
                gsheet_names = {row_values[self.column_data.racer_1], row_values[self.column_data.racer_2]}
                if gsheet_names == match_names:
                    return row+1
            return None

    def _update_cell(self, row, col, value, raw_input=True) -> bool:
        range_str = str(SheetCell(row, col, wks_name=self.wks_name))
        value_input_option = 'RAW' if raw_input else 'USER_ENTERED'
        value_range_body = {'values': [value]}
        with Spreadsheets() as spreadsheets:
            response = spreadsheets.values().update(
                spreadsheetID=self.gsheet_id,
                range=range_str,
                value_input_option=value_input_option,
                value_range_body=value_range_body
            ).execute()
            return response is not None


class TestMatchupSheet(unittest.TestCase):
    the_gsheet_id = '1JbwqUsX1ibHVVtcRVpOmaFJcfQz2ncBAOwb1nV1PsPA'

    def test_init(self):
        sheet_1 = MatchupSheet(gsheet_id=TestMatchupSheet.the_gsheet_id, wks_name='Sheet1')
        col_data = sheet_1.column_data
        self.assertEqual(col_data.tier, 2)
        self.assertEqual(col_data.racer_1, 3)
        self.assertEqual(col_data.racer_2, 4)
        self.assertEqual(col_data.date, 5)
        self.assertEqual(col_data.cawmentary, 6)
        self.assertEqual(col_data.winner, 7)
        self.assertEqual(col_data.score, 8)
        self.assertEqual(col_data.vod, 11)
        self.assertEqual(col_data.header_row, 3)
        self.assertEqual(col_data.footer_row, 6)

        sheet_2 = MatchupSheet(gsheet_id=TestMatchupSheet.the_gsheet_id, wks_name='Sheet2')
        bad_col_data = sheet_2.column_data
        self.assertIsNone(bad_col_data.header_row)

    def test_get_matches(self):
        sheet_1 = MatchupSheet(gsheet_id=TestMatchupSheet.the_gsheet_id, wks_name='Sheet1')
        matches = sheet_1.get_matches()
        self.assertEqual(len(matches), 2)
        match = matches[0]
        self.assertEqual(match.racer_1.rtmp_name, 'yjalexis')
        self.assertEqual(match.racer_2.rtmp_name, 'macnd')
