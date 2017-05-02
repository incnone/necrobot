import asyncio
import sys
import unittest

import run_condorbot
from necrobot.botbase import server

from necrobot.condor.condoradminchannel import CondorAdminChannel
from necrobot.daily.dailymgr import DailyMgr
from necrobot.ladder import ratingutil
from necrobot.ladder.ladderadminchannel import LadderAdminChannel
from necrobot.match.matchmgr import MatchMgr
from necrobot.stdconfig.mainchannel import MainBotChannel
from necrobot.stdconfig.pmbotchannel import PMBotChannel
from necrobot.util import console
from necrobot import logon

TEST_CONFIG = False
TEST_PARSE = False
TEST_SHEETS = True
TEST_USER = False

if TEST_CONFIG:
    # noinspection PyUnresolvedReferences
    from necrobot.config import TestConfig, Config

if TEST_PARSE:
    # noinspection PyUnresolvedReferences
    from necrobot.util.parse.matchparse import TestMatchParse

if TEST_SHEETS:
    # noinspection PyUnresolvedReferences
    from necrobot.gsheet.spreadsheets import TestSpreadsheets
    # noinspection PyUnresolvedReferences
    # from necrobot.gsheet.matchupsheet import TestMatchupSheet
    # noinspection PyUnresolvedReferences
    from necrobot.gsheet.sheetrange import TestSheetRange
    # noinspection PyUnresolvedReferences
    from necrobot.gsheet.standingssheet import TestStandingsSheet

if TEST_USER:
    # noinspection PyUnresolvedReferences
    from necrobot.user.necrouser import TestNecroUser


# Define client events
async def on_ready_fn(necrobot):
    sys.stdout.flush()
    await asyncio.sleep(1)

    try:
        # print(necrobot.server.me)
        unittest.main(verbosity=2)
    except SystemExit:
        pass
    finally:
        await necrobot.logout()


async def load_testing_config(necrobot):
    # PM Channel
    necrobot.register_pm_channel(PMBotChannel())

    # Main Channel
    main_discord_channel = server.find_channel(channel_name=Config.MAIN_CHANNEL_NAME)
    if main_discord_channel is None:
        console.warning('Could not find the "{0}" channel.'.format(Config.MAIN_CHANNEL_NAME))
    necrobot.register_bot_channel(main_discord_channel, MainBotChannel())

    # Condor Channel
    condor_admin_channel = server.find_channel(channel_name='condor_admin')
    if condor_admin_channel is None:
        console.warning('Could not find the "{0}" channel.'.format('condor_admin'))
    necrobot.register_bot_channel(condor_admin_channel, CondorAdminChannel())

    # Ladder Channel
    ladder_admin_channel = server.find_channel(channel_name=Config.LADDER_ADMIN_CHANNEL_NAME)
    if ladder_admin_channel is None:
        console.warning('Could not find the "{0}" channel.'.format(Config.LADDER_ADMIN_CHANNEL_NAME))
    necrobot.register_bot_channel(ladder_admin_channel, LadderAdminChannel())

    # Managers
    necrobot.register_manager(DailyMgr())
    necrobot.register_manager(MatchMgr())

    # Ratings
    ratingutil.init()


if __name__ == "__main__":
    logon.logon(
        config_filename='data/condorbot_config',
        load_config_fn=run_condorbot.load_condorbot_config,
        on_ready_fn=on_ready_fn
    )
