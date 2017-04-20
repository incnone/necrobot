import unittest
from necrobot.util import config

from necrobot.gsheet.spreadsheets import TestSpreadsheets
from necrobot.gsheet.matchupsheet import TestMatchupSheet
from necrobot.gsheet.sheetutil import TestSheetUtil

if __name__ == "__main__":
    config.init('data/bot_config')
    unittest.main(verbosity=2)
