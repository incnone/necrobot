from necrobot.util.config import Config


class RaceConfig(object):
    def __init__(
            self,
            countdown_length=Config.COUNTDOWN_LENGTH,
            unpause_countdown_length=Config.UNPAUSE_COUNTDOWN_LENGTH,
            incremental_countdown_start=Config.INCREMENTAL_COUNTDOWN_START,
            finalize_time_sec=Config.FINALIZE_TIME_SEC,
            auto_forfeit=0
    ):
        self.countdown_length = countdown_length
        self.unpause_countdown_length = unpause_countdown_length
        self.incremental_countdown_start = incremental_countdown_start
        self.finalize_time_sec = finalize_time_sec
        self.auto_forfeit = auto_forfeit
