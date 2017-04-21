import unittest

import botconfigs
import main

from necrobot.util import config
from necrobot.botbase.command import Command

from necrobot.gsheet.spreadsheets import TestSpreadsheets
from necrobot.gsheet.matchupsheet import TestMatchupSheet
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

        try:
            unittest.main(verbosity=2)
        except SystemExit as e:
            if e.code == 0:
                await the_necrobot.logout()
            else:
                raise

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
