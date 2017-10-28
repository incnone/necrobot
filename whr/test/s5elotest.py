import random
from typing import List, Tuple
import mysql.connector
from base import WholeHistoryRating


renamed_racers = {
    'narwhalman53': 'pillarmonkey',
    'abu__yazan': 'abuyazan',
    'redicewind': 'sirwuffles',
    'xelnas': 'zellyff',
    'angelica_seikai': 'angelica',
}


def add_games(whr, do_times, game_lists, test_frac=0.0):
    rand = random.Random()
    rand.seed()
    players = {}
    gametuples = []

    first_added_week = None

    if 'season_4' in game_lists:
        if first_added_week is None:
            first_added_week = 0
            week_offset = 0
        else:
            week_offset = 0 - first_added_week
        gametuples.extend(read_season4_sheet(week_offset=week_offset, do_times=do_times))
    if 'ndwc' in game_lists:
        if first_added_week is None:
            first_added_week = 27
            week_offset = 0
        else:
            week_offset = 27 - first_added_week
        gametuples.extend(read_ndwc_sheet(week_offset=week_offset, do_times=do_times))
    if 'season_5' in game_lists:
        if first_added_week is None:
            first_added_week = 56
            week_offset = 0
        else:
            week_offset = 56 - first_added_week
        gametuples.extend(read_season5_db(week_offset=week_offset, do_times=do_times))

    gametuples = sorted(gametuples, key=lambda x: x[2])
    for t in gametuples:
        p1_name = t[0].lower().rstrip(' *')
        p2_name = t[1].lower().rstrip(' *')
        if p1_name in renamed_racers:
            p1_name = renamed_racers[p1_name]
        if p2_name in renamed_racers:
            p2_name = renamed_racers[p2_name]

        if p1_name not in players:
            players[p1_name] = None
        if p2_name not in players:
            players[p2_name] = None

        for _ in range(t[3]):
            game = whr.setup_game(black=p1_name, white=p2_name, winner='B', time_step=t[2])
            whr.add_game(game=game, test=rand.random() < test_frac)
        for _ in range(t[4]):
            game = whr.setup_game(black=p2_name, white=p1_name, winner='B', time_step=t[2])
            whr.add_game(game=game, test=rand.random() < test_frac)

    return players


def read_season5_db(week_offset: int = 0, do_times: bool = True) -> List[Tuple]:
    class CondorMatch(object):
        def __init__(self, match_week, player_1, player_2, p1_wins, p2_wins):
            self.racer_1 = player_1
            self.racer_2 = player_2
            self.week = match_week
            self.races = []
            self.r1_wins = p1_wins
            self.r2_wins = p2_wins
            while p1_wins > 0:
                self.races.append(CondorRace(player_1, player_2))
                p1_wins -= 1
            while p2_wins > 0:
                self.races.append(CondorRace(player_2, player_1))
                p2_wins -= 1

    class CondorRace(object):
        def __init__(self, winner, loser):
            self.winner = winner.lower()
            self.loser = loser.lower()

    showcase_matches = [
        # Week 1 Fri
        CondorMatch(1, 'asherrose', 'the_crystal_clod', 2, 0),
        CondorMatch(1, 'ARTQ', 'yuka', 2, 1),
        CondorMatch(1, 'Echaen', 'DisgruntledGoof', 3, 0),
        CondorMatch(1, 'squega', 'moyuma', 2, 0),
        CondorMatch(1, 'JackOfGames', 'paperdoopliss', 2, 0),
        CondorMatch(1, 'incnone', 'mayantics', 2, 1),
        # Week 1 Sat
        CondorMatch(1, 'Fraxtil', 'mantasMBL', 2, 0),
        CondorMatch(1, 'naymin', 'revalize', 1, 2),
        CondorMatch(1, 'staekk', 'spootybiscuit', 1, 2),
        CondorMatch(1, 'mudjoe2', 'oblivion111', 2, 0),
        CondorMatch(1, 'spootybiscuit', 'incnone', 2, 1),
        CondorMatch(1, 'jackofgames', 'mudjoe2', 2, 0),
        # Week 2 Fri
        CondorMatch(2, 'axem', 'yuuchan', 2, 0),
        CondorMatch(2, 'bacing', 'ARTQ', 2, 0),
        CondorMatch(2, 'yuka', 'hypershock', 2, 0),
        CondorMatch(2, 'pillarmonkey', 'cyber_1', 1, 2),
        CondorMatch(2, 'spacecow2455', 'amak11', 2, 0),
        CondorMatch(2, 'paperdoopliss', 'squega', 2, 0),
        CondorMatch(2, 'staekk', 'mayantics', 1, 2),
        CondorMatch(2, 'incnone', 'paperdoopliss', 2, 0),
        # Week 2 Sat
        CondorMatch(2, 'Echaen', 'mudjoe2', 1, 2),
        CondorMatch(2, 'mayantics', 'mudjoe2', 1, 2),
        CondorMatch(2, 'naymin', 'CS1', 2, 0),
        CondorMatch(2, 'sirwuffles', 'yjalexis', 1, 2),
        CondorMatch(2, 'wonderj13', 'kingcaptain27', 2, 1),
        CondorMatch(2, 'tufwfo', 'moyuma', 1, 2),
        # Week 3 Fri
        CondorMatch(3, 'Squega', 'Echaen', 2, 1),
        CondorMatch(3, 'Midna', 'CheesiestPotato', 1, 2),
        CondorMatch(3, 'tetel', 'zellyff', 2, 0),
        CondorMatch(3, 'thalen', 'boredmai', 2, 1),
        CondorMatch(3, 'oblivion111', 'moyuma', 2, 0),
        CondorMatch(3, 'roncli', 'revalize', 2, 1),
        CondorMatch(3, 'staekk', 'paperdoopliss', 2, 0),
        # Week 3 Sat
        CondorMatch(3, 'pillarmonkey', 'fraxtil', 1, 2),
        CondorMatch(3, 'kingcaptain27', 'muffin', 2, 0),
        CondorMatch(3, 'spacecow2455', 'sponskapatrick', 1, 2),
        CondorMatch(3, 'tictacfoe', 'ARTQ', 2, 0),
        CondorMatch(3, 'slackaholicus', 'mantasmbl', 2, 0),
        CondorMatch(3, 'mayantics', 'cyber_1', 2, 0),
        CondorMatch(3, 'heather', 'pibonacci', 1, 2),
        CondorMatch(3, 'oblivion111', 'squega', 2, 0),
        CondorMatch(3, 'staekk', 'mayantics', 1, 2),
        # Week 4 Fri
        CondorMatch(4, 'greenyoshi', 'odoko_noko', 2, 0),
        CondorMatch(4, 'skullgirls', 'boredmai', 1, 2),
        CondorMatch(4, 'tufwfo', 'paratroopa1', 2, 1),
        CondorMatch(4, 'kingtorture', 'medvezhonok', 1, 2),
        CondorMatch(4, 'staekk', 'moyuma', 2, 0),
        CondorMatch(4, 'abuyazan', 'disgruntledgoof', 1, 2),
        CondorMatch(4, 'squega', 'roncli', 2, 0),
        CondorMatch(4, 'squega', 'staekk', 1, 2),
        # Week 4 Sat
        CondorMatch(4, 'tictacfoe', 'naymin', 1, 2),
        CondorMatch(4, 'yuuchan', 'teraka', 1, 2),
        CondorMatch(4, 'hypershock', 'plectro', 2, 1),
        CondorMatch(4, 'gunlovers', 'raviolinguini', 2, 0),
        CondorMatch(4, 'sirwuffles', 'asherrose', 2, 0),
        CondorMatch(4, 'pibonacci', 'pancelor', 1, 2),
        CondorMatch(4, 'artq', 'thouther', 2, 1),
        CondorMatch(4, 'echaen', 'paperdoopliss', 2, 1),
        CondorMatch(4, 'echaen', 'cyber_1', 2, 0),
        # Week 5 Fri
        CondorMatch(5, 'flygluffet', 'gfitty', 2, 1),
        CondorMatch(5, 'arboretic', 'raviolinguini', 1, 2),
        CondorMatch(5, 'disgruntledgoof', 'fraxtil', 2, 0),
        CondorMatch(5, 'pancelor', 'squega', 2, 1),
        CondorMatch(5, 'wow_tomato', 'madoka', 0, 2),
        CondorMatch(5, 'disgruntledgoof', 'pancelor', 2, 1),
        CondorMatch(5, 'kika', 'the_crystal_clod', 0, 2),
        CondorMatch(5, 'gunlovers', 'medvezhonok', 2, 0),
        # Week 5 Sat
        CondorMatch(5, 'abuyazan', 'thedarkfreaack', 0, 2),
        CondorMatch(5, 'grimy42', 'thouther', 2, 0),
        CondorMatch(5, 'plectro', 'amak11', 2, 1),
        CondorMatch(5, 'naymin', 'moyuma', 2, 1),
        CondorMatch(5, 'cyber_1', 'tufwfo', 2, 0),
        CondorMatch(5, 'naymin', 'cyber_1', 0, 2),
        CondorMatch(5, 'yuuchan', 'famslayer', 0, 2),
        CondorMatch(5, 'tictacfoe', 'necrorebel', 1, 2),
        CondorMatch(5, 'teraka', 'yuka', 0, 2),
        CondorMatch(5, 'yjalexis', 'revalize', 1, 2),
        # Play-in R1
        CondorMatch(6, 'moyuma', 'medvezhonok', 2, 0),
        CondorMatch(6, 'revalize', 'abuyazan', 2, 0),
        CondorMatch(6, 'pancelor', 'thedarkfreaack', 0, 2),
        CondorMatch(6, 'tufwfo', 'roncli', 2, 1),
        CondorMatch(6, 'tictacfoe', 'yjalexis', 1, 2),
        CondorMatch(6, 'fraxtil', 'necrorebel', 0, 2),
        CondorMatch(6, 'squega', 'gunlovers', 2, 0),
        CondorMatch(6, 'naymin', 'pibonacci', 2, 0),
        # Play-in R2
        CondorMatch(6, 'thedarkfreaack', 'tufwfo', 0, 2),
        CondorMatch(6, 'yjalexis', 'necrorebel', 2, 0),
        CondorMatch(6, 'moyuma', 'revalize', 0, 2),
        CondorMatch(6, 'squega', 'naymin', 0, 2),
        # Play-in R3
        CondorMatch(6, 'revalize', 'tufwfo', 3, 2),
        CondorMatch(6, 'yjalexis', 'naymin', 2, 3),
        # Playoff Day 1
        CondorMatch(7, 'cyber_1', 'echaen', 3, 2),
        CondorMatch(7, 'naymin', 'mayantics', 3, 2),
        CondorMatch(7, 'staekk', 'disgruntledgoof', 3, 2),
        CondorMatch(7, 'oblivion111', 'revalize', 2, 3),
        CondorMatch(7, 'mudjoe2', 'staekk', 3, 1),
        CondorMatch(7, 'staekk', 'oblivion111', 0, 2),
        # Playoff Day 2
        CondorMatch(7, 'jackofgames', 'naymin', 1, 3),
        CondorMatch(7, 'incnone', 'revalize', 3, 0),
        CondorMatch(7, 'echaen', 'jackofgames', 1, 2),
        CondorMatch(7, 'spootybiscuit', 'cyber_1', 3, 1),
        CondorMatch(7, 'oblivion111', 'echaen', 2, 0),
        CondorMatch(7, 'mayantics', 'cyber_1', 0, 2),
        CondorMatch(7, 'disgruntledgoof', 'revalize', 2, 0),
        CondorMatch(7, 'spootybiscuit', 'incnone', 0, 3),
        CondorMatch(7, 'cyber_1', 'disgruntledgoof', 2, 1),
        # Playoff Day 3
        CondorMatch(7, 'mudjoe2', 'naymin', 3, 2),
        CondorMatch(7, 'naymin', 'cyber_1', 0, 2),
        CondorMatch(7, 'incnone', 'mudjoe2', 1, 3),
        CondorMatch(7, 'spootybiscuit', 'oblivion111', 2, 0),
        CondorMatch(7, 'spootybiscuit', 'cyber_1', 2, 0),
        CondorMatch(7, 'incnone', 'spootybiscuit', 3, 2),
        CondorMatch(7, 'incnone', 'mudjoe2', 3, 1),
        CondorMatch(7, 'incnone', 'mudjoe2', 3, 0),
    ]

    mysql_db_host = 'necrobot.condorleague.tv'
    mysql_db_user = 'necrobot-read'
    mysql_db_passwd = 'necrobot-read'
    mysql_db_name = 'condor_s5'

    db_conn = mysql.connector.connect(
        user=mysql_db_user,
        password=mysql_db_passwd,
        host=mysql_db_host,
        database=mysql_db_name
    )

    try:
        cursor = db_conn.cursor()

        cursor.execute(
            """
            SELECT 
                ud1.rtmp_name AS racer_1,
                ud2.rtmp_name AS racer_2,
                week_number,
                racer_1_wins,
                racer_2_wins
            FROM 
                match_data
            JOIN
                user_data ud1 ON ud1.racer_id = match_data.racer_1_id
            JOIN
                user_data ud2 ON ud2.racer_id = match_data.racer_2_id
            WHERE
                week_number BETWEEN 1 AND 5
            """
        )

        gametuples = []

        for row in cursor:
            racer_1 = row[0].lower()
            racer_2 = row[1].lower()
            week = int(row[2]) if do_times else 1
            racer_1_wins = int(row[3])
            racer_2_wins = int(row[4])

            gametuples.append((racer_1, racer_2, week + week_offset, racer_1_wins, racer_2_wins,))
    finally:
        db_conn.close()

    for match in showcase_matches:
        week = match.week if do_times else 1
        if week + week_offset == 16:
            print('thateaaaaaaaaaaaaaaaaaaaaaahtjk')
        gametuples.append(
            (match.racer_1.lower(), match.racer_2.lower(), week + week_offset, match.r1_wins, match.r2_wins,)
        )

    return gametuples


def read_ndwc_sheet(week_offset: int = 0, do_times: bool = True) -> List[Tuple]:
    with open('condor_ndwc.csv', 'r') as file:
        content = file.readlines()

    content = [line.strip('\n') for line in content if line.startswith(',') and not line.startswith(',,')]
    games = []
    for line in content:
        values = line.split(',')
        racer_name = values[1].lower()
        racer_games = [
            (1, int(values[3]), values[10].lower(),),
            (1, int(values[4]), values[11].lower(),),
            (2, int(values[5]), values[12].lower(),),
            (2, int(values[6]), values[13].lower(),),
            (3, int(values[7]), values[14].lower(),),
            (3, int(values[8]), values[15].lower(),),
            (3, int(values[9]), values[16].lower(),),
        ]
        for game in racer_games:
            games.append((racer_name, game[2], (game[0] if do_times else 1) + week_offset, game[1], 0,))

    return games


def read_season4_sheet(week_offset: int = 0, do_times: bool = True) -> List[Tuple]:
    with open('condor_s4.csv', 'r') as file:
        content = file.readlines()

    content = [line.strip('\n') for line in content if not line.startswith(',') and not line.startswith('R')]
    games = []

    for line in content:
        values = line.split(',')
        racer_name = values[1].lower()

        for week in range(1, 7):
            num_wins_col = 2*week + 1
            opp_col = num_wins_col + 12
            try:
                games.append((
                    racer_name,
                    values[opp_col].lower(),
                    (week if do_times else 1) + week_offset,
                    int(values[num_wins_col]),
                    0,
                ))
            except ValueError:
                continue

    return games


def fit_w(whr: WholeHistoryRating, stdev: float, min_w, max_w, verbose=False):
    """Use bisection to find a good w and prior_stdev for our data."""
    from math import exp, log

    min_logw = log(min_w)
    max_logw = log(max_w)
    numsteps = 25

    best_w = None
    max_ll_so_far = None

    for step in range(numsteps):
        y = step/(numsteps-1)
        w = exp(y*max_logw + (1-y)*min_logw)
        if verbose:
            print('Computing w={}, d={}...'.format(w, stdev))
        whr.reset_config(w=w, prior_stdev=stdev)
        whr.iterate_until(elo_diff=0.1, max_cycles=200)
        ll = whr.log_likelihood_test(multiday_only=True)
        if max_ll_so_far is None or ll > max_ll_so_far:
            max_ll_so_far = ll
            best_w = w
            if verbose:
                print('Got a new maximum log-likelihood of {}.'.format(ll))
        elif verbose:
            print('Got a log-likelihood of {}.'.format(ll))

    if verbose:
        print('Best w = {}.'.format(best_w))
    return best_w


def fit_stdev(whr: WholeHistoryRating, w: float, min_d, max_d, verbose=False):
    """Use bisection to find a good w and prior_stdev for our data."""
    from math import exp, log

    min_logd = log(min_d)
    max_logd = log(max_d)
    numsteps = 15

    best_d = None
    max_ll_so_far = None

    for step in range(numsteps):
        y = step/(numsteps-1)
        stdev = exp(y*max_logd + (1-y)*min_logd)
        if verbose:
            print('Computing w={}, d={}...'.format(w, stdev))
        whr.reset_config(w=w, prior_stdev=stdev)
        whr.iterate_until(elo_diff=0.1, max_cycles=200)
        ll = whr.log_likelihood_test()
        if max_ll_so_far is None or ll > max_ll_so_far:
            max_ll_so_far = ll
            best_d = stdev
            if verbose:
                print('Got a new maximum log-likelihood of {}.'.format(ll))
        elif verbose:
            print('Got a log-likelihood of {}.'.format(ll))

    if verbose:
        print('Best w = {}.'.format(best_d))
    return best_d


def find_best_params(init_w, init_d, game_lists):
    def avg(l):
        return float(sum(l))/float(len(l))

    mean_w = init_w
    mean_d = init_d

    all_ws = []
    all_ds = []
    for trial in range(10):
        ws = []
        for i in range(15):
            the_whr = WholeHistoryRating(verbose=False, w=19.0, prior_stdev=120.0)
            the_players = add_games(the_whr, game_lists=game_lists, do_times=False, test_frac=0.5)
            w = fit_w(the_whr, stdev=mean_d, min_w=mean_w/2, max_w=mean_w*2)
            ws.append(w)
            if trial >= 5:
                all_ws.append(w)
            print('Cycle {}, w = {}'.format(i, w))

        mean_w = avg(ws)
        print('------------------Mean best w = {}-------------------'.format(mean_w))

        ds = []
        for i in range(10):
            the_whr = WholeHistoryRating(verbose=False, w=19.0, prior_stdev=600.0)
            the_players = add_games(the_whr, game_lists=game_lists, do_times=True, test_frac=0.20)
            d = fit_stdev(the_whr, w=mean_w, min_d=mean_d/2, max_d=mean_d*2)
            ds.append(d)
            if trial >= 5:
                all_ds.append(d)
            print('Cycle {}, stdev = {}'.format(i, d))

        mean_d = avg(ds)
        print('------------------Mean best dev = {}-----------------'.format(mean_d))

    print('')
    print('Average w: {}'.format(avg(all_ws)))
    print('Average d: {}'.format(avg(all_ds)))


def rate_all():
    # game_lists = ['season_4', 'ndwc', 'season_5']
    prior_stdev = 400.0
    game_lists = ['season_5']
    the_whr = WholeHistoryRating(verbose=False, w=13, prior_stdev=prior_stdev)
    the_players = add_games(the_whr, game_lists=game_lists, do_times=False, test_frac=0.0)
    the_whr.iterate_until(elo_diff=0.1, max_cycles=200)
    for player in the_players:
        ratings = the_whr.ratings_for_player(player)
        if len(ratings) == 0:
            print(player)
        the_players[player] = the_whr.ratings_for_player(player)

    with open('s5_whr.txt', 'w') as file:
        file.write('Stdev: {stdev}\n'.format(stdev=prior_stdev))
        player_format_str = '{rank:>3} {name:>20} : {rating:4.0f}  +/- {stdev:4.0f}\n'
        sorted_players = sorted(the_players.items(), key=lambda p: p[1][-1][1], reverse=True)
        rank = 0
        for name, ratings in sorted_players:
            rank += 1
            for rating in ratings:
                file.write(player_format_str.format(rank=rank, name=name, rating=rating[1], stdev=rating[2]))

    # with open('s5_whr.txt', 'w') as file:
    #     sorted_players = sorted(the_players.items(), key=lambda p: p[1][-1][1], reverse=True)
    #     day_numbers = [1, 2, 3, 4, 5, 6, 28, 29, 30, 57, 58, 59, 60, 61, 62, 63]
    #     for name, ratings in sorted_players:
    #         player_str = name + ','
    #         day_idx = -1
    #         for rating in ratings:
    #             day_idx += 1
    #             while rating[0] != day_numbers[day_idx]:
    #                 player_str += ','
    #                 day_idx += 1
    #             player_str += str(rating[1]) + ','
    #         player_str += '\n'
    #         file.write(player_str)


if __name__ == "__main__":
    rate_all()
    # find_best_params(init_w=10.0, init_d=300.0, game_lists=['season_4', 'ndwc', 'season_5'])
