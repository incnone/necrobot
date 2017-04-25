import asyncio
import sys
import unittest

from necrobot.util import loader, logon

TEST_CONFIG = False
TEST_PARSE = False
TEST_SHEETS = False
TEST_USER = False

if TEST_CONFIG:
    # noinspection PyUnresolvedReferences
    from necrobot.config import TestConfig

if TEST_PARSE:
    # noinspection PyUnresolvedReferences
    from necrobot.util.parse.matchparse import TestMatchParse

if TEST_SHEETS:
    # noinspection PyUnresolvedReferences
    from necrobot.gsheet.spreadsheets import TestSpreadsheets
    # noinspection PyUnresolvedReferences
    from necrobot.gsheet.matchupsheet import TestMatchupSheet
    # noinspection PyUnresolvedReferences
    from necrobot.gsheet.sheetrange import TestSheetRange
    # noinspection PyUnresolvedReferences
    # from necrobot.gsheet.sheetutil import TestSheetUtil

if TEST_USER:
    # noinspection PyUnresolvedReferences
    from necrobot.user.necrouser import TestNecroUser


# Define client events
async def on_ready_fn(necrobot):
    sys.stdout.flush()
    await asyncio.sleep(1)

    try:
        unittest.main(verbosity=2)
    except SystemExit:
        pass
    finally:
        await necrobot.logout()


if __name__ == "__main__":
    logon.logon(
        config_filename='data/condorbot_config',
        load_config_fn=loader.load_condorbot_config,
        on_ready_fn=on_ready_fn
    )
