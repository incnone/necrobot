from necrobot.config import Config

from necrobot.ladder.ladderchannel import LadderChannel
from necrobot.ladder.ladderadminchannel import LadderAdminChannel
from necrobot.stdconfig.mainchannel import MainBotChannel
from necrobot.stdconfig.pmbotchannel import PMBotChannel

from necrobot.daily.dailymgr import DailyMgr
from necrobot.league.leaguemgr import LeagueMgr
from necrobot.match.matchmgr import MatchMgr
from necrobot.ladder.laddermgr import LadderMgr

from necrobot.botbase import server
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
    server.main_channel = main_discord_channel
    necrobot.register_bot_channel(server.main_channel, MainBotChannel())

    # Ladder Channels
    ladder_channel = server.find_channel(Config.LADDER_CHANNEL_NAME)
    ladder_admin_channel = server.find_channel(Config.LADDER_ADMIN_CHANNEL_NAME)
    if ladder_channel is None:
        console.warning('Could not find the "{0}" channel.'.format(Config.LADDER_CHANNEL_NAME))
    if ladder_admin_channel is None:
        console.warning('Could not find the "{0}" channel.'.format(Config.LADDER_ADMIN_CHANNEL_NAME))
    necrobot.register_bot_channel(ladder_channel, LadderChannel())
    necrobot.register_bot_channel(ladder_admin_channel, LadderAdminChannel())

    # Managers
    necrobot.register_manager(DailyMgr())
    necrobot.register_manager(LeagueMgr())
    necrobot.register_manager(MatchMgr())
    necrobot.register_manager(LadderMgr())

    # # Ratings
    # ratingutil.init()


if __name__ == "__main__":
    logon.logon(
        config_filename='data/necrobot_config',
        load_config_fn=load_necrobot_config
    )

