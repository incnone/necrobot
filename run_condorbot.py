from necrobot.util import server
from necrobot.condorbot.condoradminchannel import CondorAdminChannel
from necrobot.condorbot.condormainchannel import CondorMainChannel
from necrobot.condorbot.condormgr import CondorMgr
from necrobot.condorbot.condorpmchannel import CondorPMChannel
from necrobot.ladder import ratingutil
from necrobot.league.leaguemgr import LeagueMgr
from necrobot.match.matchmgr import MatchMgr
from necrobot.util import console
from necrobot import logon
from necrobot.config import Config


async def load_condorbot_config(necrobot):
    # PM Channel
    necrobot.register_pm_channel(CondorPMChannel())

    # Main Channel
    main_channel = server.find_channel(channel_id=Config.MAIN_CHANNEL_ID)
    if main_channel is None:
        console.warning(f'Could not find the main channel <#{Config.MAIN_CHANNEL_ID}>.')
    necrobot.register_bot_channel(main_channel, CondorMainChannel(ladder=True))

    # Admin Channel
    admin_channel_name = 'adminchat'
    condor_admin_channel = server.find_channel(channel_name=admin_channel_name)
    if condor_admin_channel is None:
        console.warning(f'Could not find the admin channel "{admin_channel_name}".')
    necrobot.register_bot_channel(condor_admin_channel, CondorAdminChannel())

    # Managers (Order is important!)
    necrobot.register_manager(CondorMgr())
    necrobot.register_manager(LeagueMgr())
    necrobot.register_manager(MatchMgr())

    # Ratings
    ratingutil.init()


if __name__ == "__main__":
    logon.logon(
        config_filename='data/condorbot_config',
        logging_prefix='condorbot',
        load_config_fn=load_condorbot_config
    )
