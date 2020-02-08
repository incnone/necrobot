from typing import Optional, Union
from collections import defaultdict
from necrobot.league import leaguedb
from necrobot.gsheet.makerequest import make_request
from necrobot.gsheet.sheetrange import SheetRange
from necrobot.gsheet.spreadsheets import Spreadsheets


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
        self.wks_id = None
        self.wks_name = None

        self._not_found_matches = []
        self._offset = None
        self._sheet_size = None

    async def initialize(self, wks_name: str = None, wks_id: str = None) -> None:
        async with Spreadsheets() as spreadsheets:
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
                self.wks_id = 0

    async def overwrite_gsheet(self, league_tag: str) -> None:
        raw_data = await leaguedb.get_standings_data_raw(league_tag=league_tag)
        racers = set()
        record = defaultdict(lambda: [0, 0])
        for row in raw_data:
            if row[0] is not None and row[1] is not None:
                racers.add(row[0])
                racers.add(row[1])
                record[(row[0], row[1])][0] += row[2]
                record[(row[0], row[1])][1] += row[3]
                record[(row[1], row[0])][0] += row[3]
                record[(row[1], row[0])][1] += row[2]
        racers = sorted(racers)

        values = [[''] + list(x for x in racers)]
        for racer in racers:
            values.append([racer] + ['' for _ in range(len(racers))])

        for the_racers, the_record in record.items():
            idx = racers.index(the_racers[0]) + 1
            jdx = racers.index(the_racers[1]) + 1
            values[idx][jdx] = '{wins}-{losses}'.format(wins=the_record[0], losses=the_record[1])

        # Construct the SheetRange to update
        range_to_update = SheetRange(
            ul_cell=(1, 1),
            lr_cell=(len(racers) + 1, len(racers) + 1),
            wks_name=self.wks_name,
        )

        await self._update_cells(
            sheet_range=range_to_update,
            values=values,
            raw_input=False
        )

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
