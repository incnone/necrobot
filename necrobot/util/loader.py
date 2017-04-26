from necrobot.util import console
from necrobot.ladder import ratingutil

from necrobot.config import Config

# Necrobot channels
from necrobot.stdconfig.mainchannel import MainBotChannel
from necrobot.stdconfig.pmbotchannel import PMBotChannel

# Condorbot channels
from necrobot.condor.condoradminchannel import CondorAdminChannel
from necrobot.condor.condormainchannel import CondorMainChannel
from necrobot.condor.condorpmchannel import CondorPMChannel

# Ladder channels
from necrobot.ladder.ladderadminchannel import LadderAdminChannel

# Managers
from necrobot.daily.dailymanager import DailyManager
from necrobot.league.leaguemanager import LeagueManager
from necrobot.match.matchmanager import MatchManager


async def load_necrobot_config(necrobot):
    Config.RECORDING_ACTIVATED = False

    # PM Channel
    necrobot.register_pm_channel(PMBotChannel())

    # Main Channel
    main_discord_channel = necrobot.find_channel(Config.MAIN_CHANNEL_NAME)
    if main_discord_channel is None:
        console.warning('Could not find the "{0}" channel.'.format(Config.MAIN_CHANNEL_NAME))
    necrobot.register_bot_channel(main_discord_channel, MainBotChannel())

    # Ladder Channel
    ladder_admin_channel = necrobot.find_channel(Config.LADDER_ADMIN_CHANNEL_NAME)
    if ladder_admin_channel is None:
        console.warning('Could not find the "{0}" channel.'.format(Config.LADDER_ADMIN_CHANNEL_NAME))
    necrobot.register_bot_channel(ladder_admin_channel, LadderAdminChannel())

    # Daily Manager
    necrobot.register_manager('daily', DailyManager())
    necrobot.register_manager('match', MatchManager())

    # Ratings
    ratingutil.init()


# TODO: Make channel names changeable
async def load_condorbot_config(necrobot):
    # PM Channel
    necrobot.register_pm_channel(CondorPMChannel())

    # Main Channel
    main_discord_channel = necrobot.find_channel('season5')
    if main_discord_channel is None:
        console.warning('Could not find the "{0}" channel.'.format('season5'))
    necrobot.register_bot_channel(main_discord_channel, CondorMainChannel())

    # Admin channel
    condor_admin_channel = necrobot.find_channel('adminchat')
    if condor_admin_channel is None:
        console.warning('Could not find the "{0}" channel.'.format('adminchat'))
    necrobot.register_bot_channel(condor_admin_channel, CondorAdminChannel())

    # Managers
    necrobot.register_manager('league', LeagueManager())
    necrobot.register_manager('match', MatchManager())

    # Ratings
    ratingutil.init()


async def load_testing_config(necrobot):
    # PM Channel
    necrobot.register_pm_channel(PMBotChannel())

    # Main Channel
    main_discord_channel = necrobot.find_channel(Config.MAIN_CHANNEL_NAME)
    if main_discord_channel is None:
        console.warning('Could not find the "{0}" channel.'.format(Config.MAIN_CHANNEL_NAME))
    necrobot.register_bot_channel(main_discord_channel, MainBotChannel())

    # Condor Channel
    condor_admin_channel = necrobot.find_channel('condor_admin')
    if condor_admin_channel is None:
        console.warning('Could not find the "{0}" channel.'.format('condor_admin'))
    necrobot.register_bot_channel(condor_admin_channel, CondorAdminChannel())

    # Ladder Channel
    ladder_admin_channel = necrobot.find_channel(Config.LADDER_ADMIN_CHANNEL_NAME)
    if ladder_admin_channel is None:
        console.warning('Could not find the "{0}" channel.'.format(Config.LADDER_ADMIN_CHANNEL_NAME))
    necrobot.register_bot_channel(ladder_admin_channel, LadderAdminChannel())

    # Managers
    necrobot.register_manager('daily', DailyManager())
    necrobot.register_manager('match', MatchManager())

    # Ratings
    ratingutil.init()
