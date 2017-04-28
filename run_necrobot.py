from necrobot.config import Config
from necrobot.daily.dailymgr import DailyMgr
from necrobot.ladder import ratingutil
from necrobot.ladder.ladderadminchannel import LadderAdminChannel
from necrobot.match.matchmgr import MatchMgr
from necrobot.stdconfig.mainchannel import MainBotChannel
from necrobot.stdconfig.pmbotchannel import PMBotChannel
from necrobot.util import console
from necrobot import logon


async def load_necrobot_config(necrobot):
    Config.RECORDING_ACTIVATED = False

    # PM Channel
    necrobot.register_pm_channel(PMBotChannel())

    # Main Channel
    main_discord_channel = necrobot.find_channel(Config.MAIN_CHANNEL_NAME)
    if main_discord_channel is None:
        console.warning('Could not find the "{0}" channel.'.format(Config.MAIN_CHANNEL_NAME))
    necrobot.set_main_channel(main_discord_channel)
    necrobot.register_bot_channel(necrobot.main_channel, MainBotChannel())

    # # Ladder Channel
    # ladder_admin_channel = necrobot.find_channel(Config.LADDER_ADMIN_CHANNEL_NAME)
    # if ladder_admin_channel is None:
    #     console.warning('Could not find the "{0}" channel.'.format(Config.LADDER_ADMIN_CHANNEL_NAME))
    # necrobot.register_bot_channel(ladder_admin_channel, LadderAdminChannel())

    # Managers
    necrobot.register_manager(DailyMgr())
    # necrobot.register_manager(MatchManager())

    # # Ratings
    # ratingutil.init()


if __name__ == "__main__":
    logon.logon(
        config_filename='data/necrobot_config',
        load_config_fn=load_necrobot_config
    )

