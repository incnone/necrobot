import string
import unittest

import googleapiclient.errors

from necrobot.gsheet.makerequest import make_request
from necrobot.gsheet.spreadsheets import Spreadsheets


def num_to_colname(num: int) -> str:
    """Convert the given number to a gsheet column name.
    :param num: The column number to be converted
    :return: A string giving the name of the gsheet column (e.g. 'AB' for num=28)
    :exception IndexError: If num <= 0
    """

    if num <= 0:
        raise IndexError

    colname = ''
    while num != 0:
        mod = (num - 1) % 26
        num = int((num - mod) // 26)
        colname += string.ascii_uppercase[mod]
    return colname[::-1]    # [::-1] reverses the sequence


async def has_read_write_permissions(gsheet_id: str) -> (bool, str):
    """Checks that the bot has read/write permissions to the GSheet.
    
    Parameters
    ----------
    gsheet_id: str
        The GSheet ID.    
    
    Returns
    -------
    bool
        True if the bot has read and write permissions, False otherwise
    str
        The name of the sheet if the bot has permissions, or an error message otherwise
    """
    with Spreadsheets() as spreadsheets:
        request = spreadsheets.get(spreadsheetId=gsheet_id)
        try:
            spreadsheet = await make_request(request)
            return True, spreadsheet['properties']['title']
        except googleapiclient.errors.HttpError as e:
            # noinspection PyProtectedMember
            e_as_str = e._get_reason()
            return False, e_as_str if e_as_str else 'Unknown error.'


# class TestSheetUtil(unittest.TestCase):
#     def test_num_to_colname(self):
#         self.assertEqual(num_to_colname(1), 'A')
#         self.assertEqual(num_to_colname(5), 'E')
#         self.assertEqual(num_to_colname(26), 'Z')
#         self.assertEqual(num_to_colname(28), 'AB')
#         self.assertEqual(num_to_colname(701), 'ZY')
#         self.assertEqual(num_to_colname(704), 'AAB')
#         self.assertRaises(IndexError, num_to_colname, 0)
#
#     def test_has_read_write_permissions(self):
#         good_sheet_id = '1JbwqUsX1ibHVVtcRVpOmaFJcfQz2ncBAOwb1nV1PsPA'
#         bad_sheet_id = '1d4MpzFvMGqV-_eCfgzxua70uoNBJiBR2ge0EdAKIreQ'
#         no_sheet_id = ''
#
#         rw_good = has_read_write_permissions(gsheet_id=good_sheet_id)
#         rw_bad = has_read_write_permissions(gsheet_id=bad_sheet_id)
#         rw_none = has_read_write_permissions(gsheet_id=no_sheet_id)
#
#         self.assertTrue(rw_good[0])
#         self.assertFalse(rw_bad[0])
#         self.assertFalse(rw_none[0])
#
#         self.assertEqual(rw_good[1], 'API Testing')
#         self.assertEqual(rw_bad[1], "The caller does not have permission")
#         self.assertEqual(rw_none[1], "Not Found")
