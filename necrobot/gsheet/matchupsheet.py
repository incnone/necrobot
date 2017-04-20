import unittest

from necrobot.gsheet.sheetutil import SheetRange
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
        self.wks_name = wks_name

        # Column indicies
        self.tier = None
        self.racer_1 = None
        self.racer_2 = None
        self.date = None
        self.cawmentary = None
        self.winner = None
        self.score = None
        # self.match_type = None
        self.vod = None

        self.min_column = None
        self.max_column = None

        # Row indicies
        self.header_row = None
        self.footer_row = None

        # Call init
        self._init(gsheet_id)

    def _init(self, gsheet_id):
        with Spreadsheets() as spreadsheets:
            # Find the size of the worksheet
            sheet_size = None
            sheet_data = spreadsheets.get(spreadsheetId=gsheet_id).execute()
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
                    spreadsheetId=gsheet_id,
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
                                col += 1
                                cell_value = cell_value.lower()
                                if cell_value.startswith('racer 1'):
                                    self.racer_1 = col
                                    self.header_row = row
                                    col_vals.append(col)
                                elif cell_value.startswith('racer 2'):
                                    self.racer_2 = col
                                    self.header_row = row
                                    col_vals.append(col)
                                elif cell_value.startswith('tier'):
                                    self.tier = col
                                    col_vals.append(col)
                                elif cell_value.startswith('date'):
                                    self.date = col
                                    col_vals.append(col)
                                elif cell_value.startswith('cawmentary'):
                                    self.cawmentary = col
                                    col_vals.append(col)
                                elif cell_value.startswith('winner'):
                                    self.winner = col
                                    col_vals.append(col)
                                elif 'score' in cell_value:
                                    self.score = col
                                    col_vals.append(col)
                                elif cell_value.startswith('vod'):
                                    self.vod = col
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
    def full_range(self):
        return SheetRange(
            ul_cell=(self.header_row + 1, self.min_column,),
            lr_cell=(self.footer_row - 1, self.max_column,),
            wks_name=self.wks_name
        )

    @property
    def racer_names_range(self):
        min_col = min(self.racer_1, self.racer_2)
        max_col = max(self.racer_1, self.racer_2)
        return SheetRange(
            ul_cell=(self.header_row + 1, min_col,),
            lr_cell=(self.footer_row - 1, max_col,),
            wks_name=self.wks_name
        )


class MatchupSheet(object):
    """
    Represents a single worksheet with matchup & scheduling data.
    """

    def __init__(self, gsheet_id, wks_name=None):
        self.gsheet_id = gsheet_id
        self.wks_name = wks_name
        self.column_data = MatchupSheetIndexData(self.gsheet_id, self.wks_name)

    def get_matches(self):
        matches = []
        with Spreadsheets() as spreadsheets:
            range_to_get = self.column_data.racer_names_range
            value_range = spreadsheets.values().get(
                spreadsheetId=self.gsheet_id,
                range=range_to_get,
                majorDimension='ROWS'
            ).execute()

            if 'values' not in value_range:
                return matches

            racer_1_idx = self.column_data.racer_1 - range_to_get.left
            racer_2_idx = self.column_data.racer_2 - range_to_get.left
            for row_values in value_range['values']:
                racer_1_name = row_values[racer_1_idx]
                racer_2_name = row_values[racer_2_idx]
                racer_1 = userutil.get_user(any_name=racer_1_name)
                racer_2 = userutil.get_user(any_name=racer_2_name)
                if racer_1 is None or racer_2 is None:
                    console.error('Error finding racers for match {0}-{1}.'.format(
                        racer_1_name, racer_2_name
                    ))
                    continue
                new_match = matchutil.make_registered_match(
                    racer_1_id=racer_1.user_id,
                    racer_2_id=racer_2.user_id,
                    ranked=True
                )
                matches.append(new_match)
        return matches


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
        # sheet_1 = MatchupSheet(gsheet_id=TestMatchupSheet.the_gsheet_id, wks_name='Sheet1')
        # matches = sheet_1.get_matches()
        # for match in matches:
        #     print(match.matchroom_name)
        pass  # TODO
