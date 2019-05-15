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


async def load_condorbot_config(necrobot):
    # PM Channel
    necrobot.register_pm_channel(CondorPMChannel())

    # Main Channel
    necrobot.register_bot_channel(guild.main_channel, CondorMainChannel(ladder=True))

    # Admin Channel
    condor_admin_channel = guild.find_channel(channel_name='adminchat')
    if condor_admin_channel is None:
        console.warning('Could not find the "{0}" channel.'.format('adminchat'))
    necrobot.register_bot_channel(condor_admin_channel, CondorAdminChannel())

    # Managers (Order is important!)
    necrobot.register_manager(LeagueMgr())
    necrobot.register_manager(MatchMgr())
    necrobot.register_manager(CondorMgr())

    # Ratings
    ratingutil.init()


if __name__ == "__main__":
    logon.logon(
        config_filename='data/condorbot_config',
        logging_prefix='condorbot',
        load_config_fn=load_condorbot_config
    )
