import textwrap
from necrobot.match import matchdb
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


async def get_fastest_times_league_infotext(limit: int) -> str:
    fastest_times = await matchdb.get_fastest_wins_raw(limit)
    max_namelen = 0
    namelen_cap = 20
    for row in fastest_times:
        max_namelen = max(max_namelen, len(row[1]), namelen_cap)

    dated_format_str = '  {winner:>' + str(max_namelen) + '.' + str(max_namelen) + \
                       '} -- {time:<9} (vs {loser}, {date:%b %d})\n'
    undated_format_str = '  {winner:>' + str(max_namelen) + '.' + str(max_namelen) + \
                         '} -- {time:<9} (vs {loser})\n'

    infotext = ''
    for row in fastest_times:
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


async def get_league_stats(user_id: int) -> LeagueStats:
    stats = await matchdb.get_matchstats_raw(user_id)
    return LeagueStats(
        wins=stats[0],
        best=stats[1],
        average=stats[2],
        losses=stats[3]
    )


async def get_big_infotext(user: NecroUser, stats: LeagueStats) -> str:
    return textwrap.dedent(
        """
        {discord_name} ({userinfo})
               RTMP: {rtmp_name}
             Twitch: {twitch_name}
           Timezone: {timezone}
             Record: {wins}-{losses}
           Best win: {best_win}
           Avg. win: {avg_win}
        """.format(
            discord_name=user.display_name,
            userinfo=user.user_info,
            rtmp_name=user.rtmp_name,
            twitch_name=user.twitch_name,
            timezone=user.timezone,
            wins=stats.wins,
            losses=stats.losses,
            best_win=stats.best_win_str,
            avg_win=stats.avg_win_str
        )
    )
