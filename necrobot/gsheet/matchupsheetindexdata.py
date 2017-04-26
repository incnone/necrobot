from necrobot.gsheet.makerequest import make_request
from necrobot.gsheet.sheetrange import SheetRange
from necrobot.gsheet.spreadsheets import Spreadsheets
from necrobot.util import console


class MatchupSheetIndexData(object):
    """
    Stores the index of various columns on a CoNDOR matchup sheet.
    Call init() to read these indicies automatically from searching the sheet.
    """

    def __init__(self, gsheet_id: str, wks_name: str = None):
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

    async def initalize(self):
        with Spreadsheets() as spreadsheets:
            # Find the size of the worksheet
            sheet_size = None
            request = spreadsheets.get(spreadsheetId=self.gsheet_id)
            sheet_data = await make_request(request)
            for sheet in sheet_data['sheets']:
                props = sheet['properties']
                if props['title'] == self.wks_name:
                    sheet_size = (int(props['gridProperties']['rowCount']),
                                  int(props['gridProperties']['columnCount']),)
                    break

            if sheet_size is None:
                console.warning(
                    'Couldn\'t find a worksheet. '
                    'GSheetID: {0}, Worksheet Name: {1}.'.format(self.gsheet_id, self.wks_name))
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
                request = spreadsheets.values().get(
                    spreadsheetId=self.gsheet_id,
                    range=range_to_get,
                    majorDimension='ROWS'
                )
                value_range = await make_request(request)

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
    def valid(self):
        return self.header_row is not None and self.min_column is not None

    @property
    def racer_1(self):
        return self._racer_1 - self.min_column if self._racer_1 is not None else None

    @property
    def racer_2(self):
        return self._racer_2 - self.min_column if self._racer_2 is not None else None

    @property
    def cawmentary(self):
        return self._cawmentary - self.min_column if self._cawmentary is not None else None

    @property
    def date(self):
        return self._date - self.min_column if self._date is not None else None

    @property
    def match_type(self):
        return self._match_type - self.min_column if self._match_type is not None else None

    @property
    def score(self):
        return self._score - self.min_column if self._score is not None else None

    @property
    def tier(self):
        return self._tier - self.min_column if self._tier is not None else None

    @property
    def vod(self):
        return self._vod - self.min_column if self._vod is not None else None

    @property
    def winner(self):
        return self._winner - self.min_column if self._winner is not None else None

    @property
    def full_range(self):
        return SheetRange(
            ul_cell=(self.header_row + 1, self.min_column,),
            lr_cell=(self.footer_row - 1, self.max_column,),
            wks_name=self.wks_name
        )

    async def get_values(self, spreadsheets):
        range_to_get = self.full_range
        request = spreadsheets.values().get(
            spreadsheetId=self.gsheet_id,
            range=range_to_get,
            majorDimension='ROWS'
        )
        return await make_request(request)

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
