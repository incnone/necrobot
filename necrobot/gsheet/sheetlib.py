from typing import Optional
import necrobot.exception
from necrobot.gsheet.matchupsheet import MatchupSheet


_matchup_sheet_lib = {}
_sheets_by_id_lib = {}


async def get_sheet(gsheet_id: str, wks_name: Optional[str] = None, wks_id: Optional[str] = None) -> MatchupSheet:
    """Get the MatchupSheet representing the specified Google Worksheet
    
    Can specify either the worksheet name or the worksheet ID.
    
    Parameters
    ----------
    gsheet_id: str
        The ID of the GSheet (a long string with characters)
    wks_name: Optional[str]
        The name of the worksheet
    wks_id: Optional[str]
        The gid of the worksheet

    Returns
    -------
    MatchupSheet
    """
    if wks_name is None and wks_id is None:
        raise necrobot.exception.NotFoundException(
            "Called sheetlib.get_sheet with both wks_name and wks_id None."
        )

    if wks_id is not None and (gsheet_id, wks_id,) in _sheets_by_id_lib:
        return _sheets_by_id_lib[(gsheet_id, wks_id)]

    if wks_name is not None and (gsheet_id, wks_name,) in _matchup_sheet_lib:
        return _matchup_sheet_lib[(gsheet_id, wks_name,)]

    if wks_name is None:
        raise necrobot.exception.NotFoundException(
            "Called sheetlib.get_sheet with a wks_id={}, but no sheet of that ID found.".format(wks_id)
        )

    sheet = MatchupSheet(gsheet_id=gsheet_id)
    # noinspection PyTypeChecker
    await sheet.initialize(wks_name=wks_name)

    # Check for name changes
    if (gsheet_id, sheet.wks_id,) in _sheets_by_id_lib:
        sheet = _sheets_by_id_lib[(gsheet_id, sheet.wks_id,)]

        to_del = None
        for key, val in _matchup_sheet_lib.values():
            if val.wks_name == wks_name:
                to_del = key
                break
        if to_del is not None:
            del _matchup_sheet_lib[to_del]
            _matchup_sheet_lib[(gsheet_id, wks_name)] = sheet

        return sheet

    _matchup_sheet_lib[(gsheet_id, wks_name)] = sheet
    _sheets_by_id_lib[(gsheet_id, sheet.wks_id)] = sheet
    return sheet
