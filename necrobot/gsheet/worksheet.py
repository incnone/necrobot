"""Base class for the kind of GSheets worksheet this bot reads and writes to. Worksheet should have a header row,
specified by looking for particular names of columns (this is handled by derived classes). 

This class indexes the sheet from (0,0) at the upper-left of the row beneath the header row, down to the last row to 
contain any text in one of the indexed columns. It has convenience methods for grabbing data and updating columns
by column name. 
"""

from necrobot.gsheet import worksheetindexdata


class Worksheet(object):
    def __init__(self, gsheet_id: str):
        """
        Parameters
        ----------
        gsheet_id: str
            The ID of the GSheet on which this worksheet exists.
        """
        self.gsheet_id = gsheet_id
        self.index_data = WorksheetIndexData(gsheet_id=self.gsheet_id)

    @property
    def wks_name(self):
        return self.index_data.wks_name

    @property
    def wks_id(self):
        return self.index_data.wks_name

    async def initialize(self, wks_name: str = None, wks_id: int = None):
        await self.index_data.initialize(wks_name=wks_name, wks_id=wks_id)


