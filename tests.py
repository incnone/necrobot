import asyncio
import sys
import unittest

import botconfigs
import main

from necrobot.util import config
from necrobot.botbase.command import Command

TEST_CONFIG = False
TEST_SHEETS = True

if TEST_CONFIG:
    # noinspection PyUnresolvedReferences
    from necrobot.util.config import TestConfig

if TEST_SHEETS:
    # noinspection PyUnresolvedReferences
    # from necrobot.gsheet.spreadsheets import TestSpreadsheets
    # noinspection PyUnresolvedReferences
    # from necrobot.gsheet.matchupsheet import TestMatchupSheet
    # noinspection PyUnresolvedReferences
    # from necrobot.gsheet.sheetrange import TestSheetRange
    # noinspection PyUnresolvedReferences
    from necrobot.gsheet.sheetutil import TestSheetUtil


# Define client events
def ready_client_events(client, the_necrobot):
    # Called after the client has successfully logged in
    @client.event
    async def on_ready():
        await the_necrobot.post_login_init(
            client=client,
            server_id=config.Config.SERVER_ID,
            load_config_fn=botconfigs.load_standard_config
        )

        sys.stdout.flush()
        await asyncio.sleep(1)

        try:
            unittest.main(verbosity=2)
        except SystemExit:
            pass
        finally:
            await the_necrobot.logout()

    # Called whenever a new message is posted in any necrobot on any server
    @client.event
    async def on_message(message):
        cmd = Command(message)
        await the_necrobot.execute(cmd)

    # Called when a new member joins any server
    @client.event
    async def on_member_join(member):
        await the_necrobot.on_member_join(member)


if __name__ == "__main__":
    main.main(ready_client_events)
