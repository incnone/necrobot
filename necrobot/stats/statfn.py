import math

from necrobot.database import racedb
from necrobot.race import racetime
from necrobot.util import console
from necrobot.util.character import NDChar
from necrobot.util.singleton import Singleton


class CharacterStats(object):
    def __init__(self, ndchar):
        self._ndchar = ndchar
        self.number_of_races = 0
        self.mean = 0
        self.var = 0
        self.winrate = 0
        self.has_wins = False

    @property
    def ndchar(self):
        return self._ndchar

    @property
    def charname(self):
        return self.ndchar.name

    @property
    def stdev(self):
        return math.sqrt(self.var)

    @property
    def mean_str(self):
        if self.has_wins:
            return racetime.to_str(int(self.mean))
        else:
            return '--'

    @property
    def stdev_str(self):
        if self.has_wins:
            return racetime.to_str(int(self.stdev))
        else:
            return '--'

    def barf(self):
        console.info('{0:>10}   {1:>5}   {2:>9}  {3:>9}  {4:>6}\n'.format(
            self.charname,
            self.number_of_races,
            self.mean_str,
            self.stdev_str,
            int(self.winrate * 100)))


class GeneralStats(object):
    def __init__(self):
        self._charstats = []

    @property
    def infotext(self):
        info_text = '{0:>10}   {1:<5}   {2:<9}  {3:<9}  {4}\n'.format('', 'Races', 'Avg', 'Stdev', 'Clear%')
        for char in sorted(self._charstats, key=lambda c: c.number_of_races, reverse=True):
            info_text += '{0:>10}   {1:>5}   {2:>9}  {3:>9}  {4:>6}\n'.format(
                char.charname,
                char.number_of_races,
                char.mean_str,
                char.stdev_str,
                int(char.winrate*100))
        return info_text[:-1]

    def insert_charstats(self, char):
        self._charstats.append(char)

    def get_charstats(self, char):
        for c in self._charstats:
            if c.ndchar == char:
                return c
        return CharacterStats(char)


class StatCache(object, metaclass=Singleton):
    class CachedStats(object):
        def __init__(self):
            self.last_race_number_amplified = 0      # The number of the last race when amplified was cached
            self.last_race_number_base = 0           # The number of the last race when base was cached
            self.amplified_stats = GeneralStats()
            self.base_stats = GeneralStats()

    def __init__(self):
        self._cache = {}  # Map from discord ID's to UserStats

    def get_general_stats(self, user_id, amplified):
        last_race_number = racedb.get_largest_race_number(user_id=user_id)

        # Check whether we have an up-to-date cached version, and if so, return it
        cached_data = self.CachedStats()
        if user_id in self._cache:
            cached_data = self._cache[user_id]
            if amplified:
                if cached_data.last_race_number_amplified == last_race_number:
                    return cached_data.amplified_stats
            else:
                if cached_data.last_race_number_base == last_race_number:
                    return cached_data.base_stats

        # If here, the cache is out-of-date
        general_stats = GeneralStats()
        for row in racedb.get_allzones_race_numbers(user_id=user_id, amplified=amplified):
            char = NDChar.fromstr(row[0])
            charstats = CharacterStats(char)
            charstats.number_of_races = int(row[1])
            total_time = 0
            total_squared_time = 0
            number_of_wins = 0
            number_of_forfeits = 0
            for stat_row in racedb.get_all_racedata(user_id=user_id, char_name=char.name, amplified=amplified):
                if int(stat_row[1]) == -2:  # finish
                    time = int(stat_row[0])
                    total_time += time
                    total_squared_time += time * time
                    number_of_wins += 1
                else:
                    number_of_forfeits += 1

            if number_of_wins > 0:
                charstats.mean = total_time / number_of_wins

            if number_of_wins > 1:
                charstats.has_wins = True
                charstats.var = \
                    (total_squared_time / (number_of_wins-1)) - charstats.mean * total_time/(number_of_wins-1)

            if number_of_wins + number_of_forfeits > 0:
                charstats.winrate = number_of_wins / (number_of_wins + number_of_forfeits)

            general_stats.insert_charstats(charstats)

        # Update the cache
        if amplified:
            cached_data.last_race_number_amplified = last_race_number
            cached_data.amplified_stats = general_stats
        else:
            cached_data.last_race_number_base = last_race_number
            cached_data.base_stats = general_stats
        self._cache[user_id] = cached_data

        # Return
        return general_stats


def get_general_stats(user_id, amplified):
    return StatCache().get_general_stats(user_id, amplified)


def get_character_stats(user_id, ndchar, amplified):
    general_stats = StatCache().get_general_stats(user_id, amplified)
    return general_stats.get_charstats(ndchar)


def get_winrates(user_id_1, user_id_2, ndchar, amplified):
    stats_1 = get_character_stats(user_id_1, ndchar, amplified)
    stats_2 = get_character_stats(user_id_2, ndchar, amplified)
    if not stats_1.has_wins or not stats_2.has_wins:
        return None

    m2_minus_m1 = stats_2.mean - stats_1.mean
    sum_var = stats_1.var + stats_2.var
    erf_arg = m2_minus_m1 / math.sqrt(2*sum_var)
    if m2_minus_m1 > 0:
        winrate_of_1_if_both_finish = (1.0 + math.erf(erf_arg))/2.0
    else:
        winrate_of_1_if_both_finish = (1.0 - math.erf(-erf_arg))/2.0

    both_finish_prob = stats_1.winrate * stats_2.winrate
    neither_finish_prob = (1-stats_1.winrate)*(1-stats_2.winrate)
    winrate_of_1 = winrate_of_1_if_both_finish*both_finish_prob + (stats_1.winrate - both_finish_prob)
    winrate_of_2 = (1.0-winrate_of_1_if_both_finish)*both_finish_prob + (stats_2.winrate - both_finish_prob)
    return winrate_of_1, winrate_of_2, neither_finish_prob


def get_most_races_infotext(ndchar, limit):
    most_races = racedb.get_most_races_leaderboard(str(ndchar), limit)
    infotext = '{0:>16} {1:>6} {2:>6}\n'.format('', 'Base', 'Amp')
    for row in most_races:
        infotext += '{0:>16} {1:>6} {2:>6}\n'.format(row[0], row[2], row[3])
    return infotext


def get_fastest_times_infotext(ndchar, amplified, limit):
    fastest_times = racedb.get_fastest_times_leaderboard(str(ndchar), amplified, limit)
    infotext = '{0:>16} {1:<9} {2:<9} {3:<13}\n'.format('', 'Time (rta)', 'Seed', 'Date')
    for row in fastest_times:
        infotext += '{0:>16} {1:>9} {2:>9} {3:>13}\n'.format(
            row[0],
            racetime.to_str(int(row[1])),
            row[2],
            row[3].strftime("%b %d, %Y"))
    return infotext
