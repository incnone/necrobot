from necrobot.gsheet.sheetrange import SheetRange
from necrobot.gsheet.worksheetindexdata import WorksheetIndexData
from necrobot.race import racedb
from necrobot.speedrun import speedrundb
from necrobot.user import userlib


class SpeedrunSheetIndexData(WorksheetIndexData):
    def __init__(self, gsheet_id: str):
        WorksheetIndexData.__init__(
            self,
            gsheet_id=gsheet_id,
            columns=[
                'run id',
                'racer',
                'time',
                'date',
                'vod',
            ]
        )


class SpeedrunSheet(object):
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
        self.column_data = SpeedrunSheetIndexData(gsheet_id=self.gsheet_id)

    @property
    def wks_name(self):
        return self.column_data.wks_name

    @property
    def wks_id(self):
        return self.column_data.wks_id

    async def initialize(self, wks_name: str = None, wks_id: str = None):
        await self.column_data.initialize(wks_name=wks_name, wks_id=wks_id)

    async def overwrite_gsheet(self):
        await self.column_data.refresh_all()
        header_row = ['Run ID', 'Racer', 'Category', 'Time', 'Date', 'Vod']

        # Get the match data
        speedrun_data = await speedrundb.get_raw_data()

        # Construct the SheetRange to update
        range_to_update = SheetRange(
            ul_cell=(1, 1),
            lr_cell=(len(speedrun_data) + 1, len(header_row)),
            wks_name=self.wks_name,
        )

        # Construct the value array to place in the sheet
        values = [header_row]
        for raw_entry in speedrun_data:
            run_id = raw_entry[0]
            user_id = raw_entry[1]
            run_type_id = raw_entry[2]
            run_time = raw_entry[3]
            vod_url = raw_entry[4]
            submission_time = raw_entry[5]
            verified_bool = raw_entry[6]

            # Convert user ID to a username
            racer_user = await userlib.get_user(user_id=user_id)

            # Convert run type to a string
            race_info = await racedb.get_race_info_from_type_id(race_type=run_type_id)
            race_info_str = race_info.descriptor

            # Convert verified info to string
            verified_str = 'Yes' if verified_bool else 'No'

            values.append([
                run_id,
                racer_user.display_name,
                race_info_str,
                run_time,
                vod_url,
                submission_time,
                verified_str
            ])

        await self.column_data.update_cells(
            sheet_range=range_to_update,
            values=values,
            raw_input=False
        )
