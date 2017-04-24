import asyncio
import sys
import unittest

from necrobot import config, loader, logon

from necrobot.botbase.command import Command

TEST_CONFIG = False
TEST_PARSE = True
TEST_SHEETS = False

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
    from necrobot.gsheet.sheetutil import TestSheetUtil


# Define client events
def ready_client_events(client, the_necrobot, load_config_fn):
    # Called after the client has successfully logged in
    @client.event
    async def on_ready():
        await the_necrobot.post_login_init(
            client=client,
            server_id=config.Config.SERVER_ID,
            load_config_fn=load_config_fn
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
    logon.logon(
        config_filename='data/necrobot_config',
        load_config_fn=loader.load_testing_config,
        def_events_fn=ready_client_events
    )
