import discord

from necrobot.user import userutil
from necrobot.util import level, racetime

from necrobot.user.necrouser import NecroUser
from necrobot.race.racerstatus import RacerStatus

FIELD_UNKNOWN = int(-1)


class Racer(object):
    def __init__(self, member: discord.Member):
        self._user = None
        self._discord_id = int(member.id)
        self._state = RacerStatus.unready       # see RacerState notes above
        self.time = FIELD_UNKNOWN               # hundredths of a second
        self.igt = FIELD_UNKNOWN                # hundredths of a second
        self.level = level.LEVEL_NOS            # level of death (or LEVEL_FINISHED or LEVEL_UNKNOWN_DEATH)
        self.comment = ''                       # a comment added with .comment

    async def initialize(self):
        self._user = await userutil.get_user(discord_id=self._discord_id, register=True)

    @property
    def user(self) -> NecroUser:
        return self._user

    @property
    def member(self) -> discord.Member:
        return self.user.member

    @property
    def name(self) -> str:
        return self.member.display_name

    @property
    def user_id(self) -> int:
        return self.user.user_id

    @property
    def status_str(self) -> str:
        return self._status_str(False)

    @property
    def short_status_str(self) -> str:
        return self._status_str(True)
    
    def _status_str(self, short: bool) -> str:
        status = ''
        if self._state == RacerStatus.finished:
            status += racetime.to_str(self.time)
            if not self.igt == FIELD_UNKNOWN and not short:
                status += ' (igt {})'.format(racetime.to_str(self.igt))
        else:
            status += str(self._state)
            if self._state == RacerStatus.forfeit and not short:
                status += ' (rta {}'.format(racetime.to_str(self.time))
                if 0 < self.level < 22:
                    status += ', ' + level.to_str(self.level)
                if not self.igt == FIELD_UNKNOWN:
                    status += ', igt {}'.format(racetime.to_str(self.igt))
                status += ')'

        if not self.comment == '' and not short:
            status += ': ' + self.comment

        return status

    @property
    def time_str(self) -> str:
        return racetime.to_str(self.time)

    @property
    def is_ready(self) -> bool:
        return self._state == RacerStatus.ready

    @property
    def has_begun(self) -> bool:
        return self._state > RacerStatus.ready

    @property
    def is_racing(self) -> bool:
        return self._state == RacerStatus.racing

    @property
    def is_forfeit(self) -> bool:
        return self._state == RacerStatus.forfeit

    @property
    def is_finished(self) -> bool:
        return self._state == RacerStatus.finished

    @property
    def is_done_racing(self) -> bool:
        return self._state > RacerStatus.racing

    def ready(self) -> bool:
        if self._state == RacerStatus.unready:
            self._state = RacerStatus.ready
            return True
        return False

    def unready(self) -> bool:
        if self._state == RacerStatus.ready:
            self._state = RacerStatus.unready
            return True
        return False

    def begin_race(self) -> bool:
        if self._state == RacerStatus.ready:
            self._state = RacerStatus.racing
            return True
        return False

    def forfeit(self, time) -> bool:
        if self._state == RacerStatus.racing or self._state == RacerStatus.finished:
            self._state = RacerStatus.forfeit
            self.time = time
            self.level = level.LEVEL_UNKNOWN_DEATH
            self.igt = FIELD_UNKNOWN
            return True
        return False

    def unforfeit(self) -> bool:
        if self._state == RacerStatus.forfeit:
            self._state = RacerStatus.racing
            self.time = FIELD_UNKNOWN
            self.igt = FIELD_UNKNOWN
            self.level = level.LEVEL_NOS
            return True
        return False

    def finish(self, time) -> bool:
        if self._state == RacerStatus.racing or self._state == RacerStatus.forfeit:
            self._state = RacerStatus.finished
            self.time = time
            self.level = level.LEVEL_FINISHED
            return True
        return False
            
    def unfinish(self) -> bool:
        if self._state == RacerStatus.finished:
            self._state = RacerStatus.racing
            self.time = FIELD_UNKNOWN
            self.igt = FIELD_UNKNOWN
            self.level = level.LEVEL_NOS
            return True
        return False

    def add_comment(self, comment: str):
        self.comment = comment
