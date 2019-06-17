from necrobot.util import server
from necrobot.config import Config
# from necrobot.ladder import ratingutil
# from necrobot.ladder.ladderadminchannel import LadderAdminChannel
# from necrobot.ladder.laddermainchannel import LadderMainChannel
# from necrobot.league.leaguemgr import LeagueMgr
# from necrobot.match.matchmgr import MatchMgr
from necrobot.racebot.mainchannel import MainBotChannel
from necrobot.racebot.pmbotchannel import PMBotChannel
from necrobot.util import console
from necrobot import logon


async def load_necrobot_config(necrobot):
    Config.RECORDING_ACTIVATED = False

    # PM Channel
    necrobot.register_pm_channel(PMBotChannel())

    # Main Channel
    main_discord_channel = server.find_channel(channel_name=Config.MAIN_CHANNEL_NAME)
    if main_discord_channel is None:
        console.warning('Could not find the "{0}" channel.'.format(Config.MAIN_CHANNEL_NAME))
    necrobot.register_bot_channel(main_discord_channel, MainBotChannel())

    # Ladder Channels
    # ladder_main_channel = server.find_channel(Config.LADDER_MAIN_CHANNEL_NAME)
    # if ladder_main_channel is None:
    #     console.warning('Could not find the "{0}" channel.'.format(Config.LADDER_MAIN_CHANNEL_NAME))
    # ladder_admin_channel = server.find_channel(Config.LADDER_ADMIN_CHANNEL_NAME)
    # if ladder_admin_channel is None:
    #     console.warning('Could not find the "{0}" channel.'.format(Config.LADDER_ADMIN_CHANNEL_NAME))
    #
    # if ladder_main_channel is not None and ladder_admin_channel is not None:
    #     necrobot.register_bot_channel(ladder_main_channel, LadderMainChannel())
    #     necrobot.register_bot_channel(ladder_admin_channel, LadderAdminChannel())
    #
    # Config.MATCH_CHANNEL_CATEGORY_NAME = 'Ladder rooms'

    # Managers
    # necrobot.register_manager(LeagueMgr())
    # necrobot.register_manager(MatchMgr())

    # Ratings
    # ratingutil.init()


if __name__ == "__main__":
    logon.logon(
        config_filename='data/necrobot_config',
        logging_prefix='necrobot',
        load_config_fn=load_necrobot_config
    )

