import textwrap
from necrobot.league import leaguedb
from necrobot.user.necrouser import NecroUser
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


async def get_fastest_times_league_infotext(league_tag: str, limit: int) -> str:
    fastest_times = await leaguedb.get_fastest_wins_raw(league_tag, limit)
    max_namelen = 0
    namelen_cap = 20
    for row in fastest_times:
        if row[1] is None:
            continue
        max_namelen = max(max_namelen, len(row[1]), namelen_cap)

    dated_format_str = '  {winner:>' + str(max_namelen) + '.' + str(max_namelen) + \
                       '} -- {time:<9} (vs {loser}, {date:%b %d})\n'
    undated_format_str = '  {winner:>' + str(max_namelen) + '.' + str(max_namelen) + \
                         '} -- {time:<9} (vs {loser})\n'

    infotext = ''
    for row in fastest_times:
        if row[1] is None or row[2] is None:
            continue
        if row[3] is not None:
            infotext += dated_format_str.format(
                winner=row[1],
                time=racetime.to_str(row[0]),
                loser=row[2],
                date=row[3]
            )
        else:
            infotext += undated_format_str.format(
                winner=row[1],
                time=racetime.to_str(row[0]),
                loser=row[2]
            )
    return infotext[:-1] if infotext else ''


async def get_league_stats(league_tag: str, user_id: int) -> LeagueStats:
    stats = await leaguedb.get_matchstats_raw(league_tag, user_id)
    return LeagueStats(
        wins=stats[0],
        best=stats[1],
        average=stats[2],
        losses=stats[3]
    )


async def get_big_infotext(user: NecroUser, stats: LeagueStats) -> str:
    return textwrap.dedent(
        f"""
        {user.name_and_info_text}
             Twitch: {user.twitch_name}
           Timezone: {user.timezone}
             Record: {stats.wins}-{stats.losses}
           Best win: {stats.best_win_str}
           Avg. win: {stats.avg_win_str}
        """
    )
