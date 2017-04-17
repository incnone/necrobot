from necrobot.util import console
from necrobot.util.config import Config

from necrobot.daily.dailymanager import DailyManager
from necrobot.necrobot.mainchannel import MainBotChannel
from necrobot.necrobot.pmbotchannel import PMBotChannel
from necrobot.race.match import matchroom


def load_standard_config(necrobot):
    main_discord_channel = necrobot.find_channel(Config.MAIN_CHANNEL_NAME)
    if main_discord_channel is None:
        console.error('Could not find the "{0}" channel.'.format(Config.MAIN_CHANNEL_NAME))
        exit(1)

    necrobot.register_bot_channel(main_discord_channel, MainBotChannel())
    necrobot.register_pm_channel(PMBotChannel())

    necrobot.register_manager('daily', DailyManager())
    matchroom.recover_stored_match_rooms()

