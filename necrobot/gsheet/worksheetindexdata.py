import necrobot.exception
from necrobot.gsheet.makerequest import make_request
from necrobot.gsheet.sheetrange import SheetRange
from necrobot.gsheet.spreadsheets import Spreadsheets


class WorksheetIndexData(object):
    """
    Stores the index of various columns on a GSheet.
    Call initialize() to read these indicies automatically from searching the sheet.
    """

    def __init__(self, gsheet_id: str):
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
        self._col_indicies = dict()

    def __getattr__(self, item):
        return self._col_indicies[item]

    async def initialize(self, wks_name: str, wks_id: int) -> None:
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


