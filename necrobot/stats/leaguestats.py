import textwrap
from necrobot.util import racetime


class LeagueStats(object):
    def __init__(self, wins: int, losses: int, average: int, best: int):
        self.wins = wins
        self.losses = losses
        self.average = average
        self.best = best

    @property
    def best_win_str(self):
        return racetime.to_str(self.best) if self.best is not None else '--'

    @property
    def avg_win_str(self):
        return racetime.to_str(self.average) if self.average is not None else '--'

    @property
    def infotext(self) -> str:
        return textwrap.dedent(
            """
                Record: {wins}-{losses}
              Best win: {best}
              Avg. win: {avg}
            """
            .format(
                wins=self.wins,
                losses=self.losses,
                best=self.best_win_str,
                avg=self.avg_win_str
            )
        )
