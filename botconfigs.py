from necrobot.util import console
from necrobot.ladder import ratingutil
from necrobot.match import matchutil

from necrobot.util.config import Config

from necrobot.daily.dailymanager import DailyManager

from necrobot.stdconfig.mainchannel import MainBotChannel
from necrobot.stdconfig.pmbotchannel import PMBotChannel
from necrobot.condor.condoradminchannel import CondorAdminChannel
from necrobot.ladder.ladderadminchannel import LadderAdminChannel


async def load_standard_config(necrobot):
    # PM Channel
    necrobot.register_pm_channel(PMBotChannel())

    # Main Channel
    main_discord_channel = necrobot.find_channel(Config.MAIN_CHANNEL_NAME)
    if main_discord_channel is None:
        console.error('Could not find the "{0}" channel.'.format(Config.MAIN_CHANNEL_NAME))
    necrobot.register_bot_channel(main_discord_channel, MainBotChannel())

    # Ladder Channel
    ladder_admin_channel = necrobot.find_channel(Config.LADDER_ADMIN_CHANNEL_NAME)
    if ladder_admin_channel is None:
        console.error('Could not find the "{0}" channel.'.format(Config.LADDER_ADMIN_CHANNEL_NAME))
    necrobot.register_bot_channel(ladder_admin_channel, LadderAdminChannel())

    # Daily Manager
    necrobot.register_manager('daily', DailyManager())

    # Match Rooms
    await matchutil.recover_stored_match_rooms()

    # Ratings
    ratingutil.init()


async def load_testing_config(necrobot):
    # PM Channel
    necrobot.register_pm_channel(PMBotChannel())

    # Main Channel
    main_discord_channel = necrobot.find_channel(Config.MAIN_CHANNEL_NAME)
    if main_discord_channel is None:
        console.error('Could not find the "{0}" channel.'.format(Config.MAIN_CHANNEL_NAME))
    necrobot.register_bot_channel(main_discord_channel, MainBotChannel())

    # Condor Channel
    condor_admin_channel = necrobot.find_channel('condor_admin')
    if condor_admin_channel is None:
        console.error('Could not find the "{0}" channel.'.format('condor_admin'))
    necrobot.register_bot_channel(condor_admin_channel, CondorAdminChannel())

    # Ladder Channel
    ladder_admin_channel = necrobot.find_channel(Config.LADDER_ADMIN_CHANNEL_NAME)
    if ladder_admin_channel is None:
        console.error('Could not find the "{0}" channel.'.format(Config.LADDER_ADMIN_CHANNEL_NAME))
    necrobot.register_bot_channel(ladder_admin_channel, LadderAdminChannel())

    # Daily Manager
    necrobot.register_manager('daily', DailyManager())

    # Match Rooms
    await matchutil.recover_stored_match_rooms()

    # Ratings
    ratingutil.init()

