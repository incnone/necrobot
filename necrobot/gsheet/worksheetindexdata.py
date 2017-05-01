import typing
import necrobot.exception
from necrobot.gsheet.makerequest import make_request
from necrobot.gsheet.sheetcell import SheetCell
from necrobot.gsheet.sheetrange import SheetRange
from necrobot.gsheet.spreadsheets import Spreadsheets


class WorksheetIndexData(object):
    """
    Stores the index of various columns on a GSheet.
    Call initialize() to read these indicies automatically from searching the sheet.
    """

    def __init__(self, gsheet_id: str, columns: typing.List[str]):
        # Sheet info
        self.gsheet_id = gsheet_id
        self.wks_name = None
        self.wks_id = None
        self._sheet_size = None

        # Array bounds
        self.min_column = None
        self.max_column = None
        self.header_row = None
        self.footer_row = None

        # Column indicies
        self._col_names = columns
        self._col_indicies = dict()

    def __getattr__(self, item):
        return self.getcol(item)

    @property
    def col_indicies(self):
        return self._col_indicies

    def getcol(self, colname) -> int or None:
        if colname in self._col_indicies:
            return self._col_indicies[colname] - self.min_column
        else:
            return None

    def reset(self, columns: typing.List[str]) -> None:
        """Sets new column names and wipes all data."""
        self.wks_name = None
        self.wks_id = None
        self._sheet_size = None

        # Array bounds
        self.min_column = None
        self.max_column = None
        self.header_row = None
        self.footer_row = None

        # Column indicies
        self._col_names = columns
        self._col_indicies = dict()

    async def initialize(self, wks_name: str, wks_id: str) -> None:
        """Read the GSheet and store the indicies of columns
        
        Parameters
        ----------
        wks_name: str
            The name of the worksheet to initialize from.
        wks_id: int
            The ID of the worksheet to initialize from.
        
        Raises
        ------
        googleapiclient.error.Error
            Uncaught Google API error.
        AlreadyInitializedException
            If we've already called initialize() on this object
        NotFoundException
            If cannot find a worksheet with name wks_name
        """
        if self.wks_id is not None:
            raise necrobot.exception.AlreadyInitializedExecption(
                'Worksheet already initialized <wks_name = {]> <wks_id = {}>'.format(self.wks_name, self.wks_id)
            )

        async with Spreadsheets() as spreadsheets:
            # Find the size of the worksheet
            request = spreadsheets.get(spreadsheetId=self.gsheet_id)
            sheet_data = await make_request(request)
            for sheet in sheet_data['sheets']:
                props = sheet['properties']
                if wks_name is not None and props['title'] == wks_name:
                    self.wks_name = wks_name
                    self.wks_id = props['sheetId']
                    self._sheet_size = (int(props['gridProperties']['rowCount']),
                                        int(props['gridProperties']['columnCount']),)
                    break
                elif wks_id is not None and props['sheetId'] == wks_id:
                    self.wks_name = props['title']
                    self.wks_id = wks_id
                    self._sheet_size = (int(props['gridProperties']['rowCount']),
                                        int(props['gridProperties']['columnCount']),)
                    break

            if self.wks_id is None:
                raise necrobot.exception.NotFoundException(
                    "No worksheet with name {wks_name} on GSheet {gsheetid}".format(
                        wks_name=wks_name,
                        gsheetid=self.gsheet_id
                    )
                )

            await self._refresh(spreadsheets)

    @property
    def valid(self):
        return self.header_row is not None and self.min_column is not None

    @property
    def bottom_idx(self):
        return self.footer_row - self.header_row - 2

    @property
    def full_range(self):
        return SheetRange(
            ul_cell=(self.header_row + 1, self.min_column,),
            lr_cell=(self.footer_row - 1, self.max_column,),
            wks_name=self.wks_name
        )

    @property
    def full_range_extend_right(self):
        return SheetRange(
            ul_cell=(self.header_row + 1, self.min_column,),
            lr_cell=(self.footer_row - 1, self._sheet_size[1],),
            wks_name=self.wks_name
        )

    def get_range(self, left, right, top, bottom) -> SheetRange:
        return SheetRange(
            ul_cell=(self.header_row + top + 1, self.min_column + left,),
            lr_cell=(self.header_row + bottom + 1, self.min_column + right,),
            wks_name=self.wks_name
        )

    def get_range_for_column(self, col_idx):
        return self.get_range(left=col_idx, right=col_idx, top=0, bottom=self.footer_row - 1)

    async def get_values(self, spreadsheets, extend_right=False):
        range_to_get = self.full_range_extend_right if extend_right else self.full_range
        request = spreadsheets.values().get(
            spreadsheetId=self.gsheet_id,
            range=range_to_get,
            majorDimension='ROWS'
        )
        return await make_request(request)

    async def refresh_all(self):
        """Refresh all data"""
        async with Spreadsheets() as spreadsheets:
            # Find the size of the worksheet
            request = spreadsheets.get(spreadsheetId=self.gsheet_id)
            sheet_data = await make_request(request)
            for sheet in sheet_data['sheets']:
                props = sheet['properties']
                if props['sheetId'] == self.wks_id:
                    self.wks_name = props['title']
                    self._sheet_size = (int(props['gridProperties']['rowCount']),
                                        int(props['gridProperties']['columnCount']),)
                    break

            await self._refresh_all(spreadsheets)

    async def refresh_footer(self):
        """Refresh the self.footer_row property from the GSheet"""
        async with Spreadsheets() as spreadsheets:
            # Find the header row and the column indicies
            row_query_min = 1
            row_query_max = 10
            while self.footer_row is None and row_query_min <= self._sheet_size[0]:
                # Get the cells
                range_to_get = SheetRange(
                    ul_cell=(row_query_min, 1,),
                    lr_cell=(row_query_max, self._sheet_size[1],),
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
                    # If we got fewer than the requested number of rows, we've found the footer
                    if len(values) < row_query_max - row_query_min + 1:
                        self.footer_row = row_query_min + len(values)

                # Prepare for next loop
                row_query_min = row_query_max + 1
                row_query_max = min(2*row_query_max, self._sheet_size[0])

    async def update_cell(self, row: int, col: int, value: str, raw_input: bool = True) -> bool:
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
        if not self.valid:
            raise RuntimeError('Trying to update a cell on an invalid MatchupSheet.')

        row += self.header_row + 1
        col += self.min_column
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

    async def update_cells(self, sheet_range: SheetRange, values: list, raw_input=True) -> bool:
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
        if not self.valid:
            raise RuntimeError('Trying to update a cell on an invalid MatchupSheet.')

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

    async def _refresh(self, spreadsheets):
        """Find the array bounds and the column indicies"""
        # Find the header row and the column indicies
        row_query_min = 1
        row_query_max = 10
        col_vals = []
        while self.footer_row is None and row_query_min <= self._sheet_size[0]:
            # Get the cells
            range_to_get = SheetRange(
                ul_cell=(row_query_min, 1,),
                lr_cell=(row_query_max, self._sheet_size[1],),
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
                            col += 1
                            if self._make_index(cell_value, col):
                                self.header_row = row
                                col_vals.append(col)

                # If we got fewer than the requested number of rows, we've found the footer
                if len(values) < row_query_max - row_query_min + 1:
                    self.footer_row = row_query_min + len(values)

            # Prepare for next loop
            row_query_min = row_query_max + 1
            row_query_max = min(2 * row_query_max, self._sheet_size[0])

        if col_vals:
            self.min_column = min(self.min_column, min(col_vals)) if self.min_column is not None else min(col_vals)
            self.max_column = max(self.max_column, max(col_vals)) if self.max_column is not None else max(col_vals)

    def _make_index(self, cell_value: str, col: int) -> bool:
        for colname in self._col_names:
            if colname.lower() in cell_value.lower():
                self._col_indicies[self._convert_colname(colname)] = col
                return True
        return False

    @staticmethod
    def _convert_colname(c):
        return c.replace(' ', '_')
