from enum import IntEnum


class RacerStatus(IntEnum):
    """The status (racing/forfeit/etc) of the current racer.
    
    Allowable transitions are:
       unready <--> ready      (use ready() and unready())
       ready    --> racing     (use begin_race())
       racing  <--> forfeit    (use forfeit() and unforfeit())
       racing  <--> finished   (use finish() and unfinish())
    
    Values
    ------
    unready
        The racer is not yet ready to begin the race.
    ready
        The racer is ready to begin the race (but the race has not begun). Can still revert to unready.
    racing
        The racer is currently racing.
    forfeit
        The racer has forfeit the race.
    finished
        The racer has finished the race.     
    """

    unready = 1
    ready = 2
    racing = 3
    forfeit = 4
    finished = 5

    def __str__(self):
        status_strs = {
            RacerStatus.unready: 'Not ready.',
            RacerStatus.ready: 'Ready!',
            RacerStatus.racing: 'Racing!',
            RacerStatus.forfeit: 'Forfeit!',
            RacerStatus.finished: ''
        }
        return status_strs[self]
