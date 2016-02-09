import level
import racetime

RacerStatus = {'unready':1, 'ready':2, 'racing':3, 'forfeit':4, 'finished':5}
RacerStatusInv = {'1':'Not ready.', '2':'Ready!', '3':'Racing!', '4':'Forfeit', '5':''}
## Remark: code below depends on the post-begin states (3,4,5) being higher numbers than the pre-begin states (1,2)
## Allowable transitions are:
##        unready <--> ready      (use ready() and unready())
##        ready    --> racing     (use begin_race())
##        racing  <--> forfeit    (use forfeit() and unforfeit())
##        racing  <--> finished   (use finish() and unfinish())

class Racer(object):
    
    def __init__(self, member):
        self.member = member    #the Discord member who is this racer
        self._state = 1         #see RacerState notes above
        self.time = int(-1)     #hundredths of a second
        self.igt = int(-1)      #hundredths of a second
        self.level = int(-1)    #level of death (set to 18 for a win, 0 for unknown death)
        self.comment = ''       #a comment added with .comment

    @property
    def name(self):
        return self.member.name

    @property
    def id(self):
        return self.member.id

    @property
    def status_str(self):
        status = ''
        if self._state == RacerStatus['finished']:
            status += racetime.to_str(self.time)
            if not self.igt == -1:
                status += ' (igt {})'.format(racetime.to_str(self.igt))
        else:
            status += RacerStatusInv[str(self._state)]
            if self._state == RacerStatus['forfeit']:
                status += ' (rta {}'.format(racetime.to_str(self.time))
                if self.level > 0 and self.level < 18:
                    status += ', ' + level.to_str(self.level)
                if not self.igt == -1:
                    status += ', igt {}'.format(racetime.to_str(self.igt))
                status += ')'

        if not self.comment == '':
            status += ': ' + self.comment

        return status

    @property
    def time_str(self):
        return racetime.to_str(self.time)

    @property
    def is_ready(self):
        return self._state == RacerStatus['ready']

    @property
    def has_begun(self):
        return self._state > RacerStatus['ready']

    @property
    def is_racing(self):
        return self._state == RacerStaus['racing']

    @property
    def is_forfeit(self):
        return self._state == RacerStatus['forfeit']

    @property
    def is_finished(self):
        return self._state == RacerStatus['finished']

    @property
    def is_done_racing(self):
        return self._state > RacerStatus['racing']

    def ready(self):
        if self._state == RacerStatus['unready']:
            self._state = RacerStatus['ready']
            return True
        return False

    def unready(self):
        if self._state == RacerStatus['ready']:
            self._state = RacerStatus['unready']
            return True
        return False

    def begin_race(self):
        if self._state == RacerStatus['ready']:
            self._state = RacerStatus['racing']
            return True
        return False

    def forfeit(self, time):
        if self._state == RacerStatus['racing'] or self._state == RacerStatus['finished']:
            self._state = RacerStatus['forfeit']
            self.time = time
            self.level = 0
            self.igt = int(-1)
            return True
        return False

    def unforfeit(self):
        if self._state == RacerStatus['forfeit']:
            self._state = RacerStatus['racing']
            self.time = int(-1)
            self.igt = int(-1)
            self.level = int(-1)
            return True
        return False

    def finish(self, time):
        if self._state == RacerStatus['racing']:
            self._state = RacerStatus['finished']
            self.time = time
            self.level = 18
            return True
        return False
            
    def unfinish(self):
        if self._state == RacerStatus['finished']:
            self._state = RacerStatus['racing']
            self.time = int(-1)
            self.igt = int(-1)
            self.level = int(-1)
            return True
        return False

    def add_comment(self, comment):
        self.comment = comment
        
