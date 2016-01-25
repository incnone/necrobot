import command
import config
import daily

class DailyModule(command.Module):
    def __init__(self, necrobot, db_connection):
        self._necrobot = necrobot
        self._db_conn = db_connection
        self._spoilerchat_channel = necrobot.find_channel(config.DAILY_SPOILERCHAT_CHANNEL_NAME)
        self._leaderboard_channel = necrobot.find_channel(config.DAILY_LEADERBOARDS_CHANNEL_NAME)

    @property
    def infostr(self):
        return 'Speedrun daily.'

    def execute(self, command):
                    
        
