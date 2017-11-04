import math
import pulp
import random
from typing import Dict, List, Tuple

from necrobot.ladder.rating import Rating

rand = random.Random()
rand.seed()


def get_utility(r1: Rating, r2: Rating) -> float:
    prob_p1_wins = 1 / (1 + pow(10, (r2.mu - r1.mu) / 400))
    entropy = -(prob_p1_wins * math.log2(prob_p1_wins) + (1 - prob_p1_wins) * math.log2(1 - prob_p1_wins))
    return math.sqrt(entropy)


def get_matchups(
        ratings: Dict[int, Rating],
        max_matches: Dict[int, int],
        costs: Dict[Tuple[int, int], float],
        cost_multipliers: Dict[int, float]
)-> List[Tuple[int, int]]:
    prob = pulp.LpProblem("Matchup problem", pulp.LpMaximize)

    # Pre-optimize by forcing max_matches to have an even sum
    sum_matches = 0
    max_num_desired = 0
    for player, num_desired in max_matches.items():
        sum_matches += num_desired
        max_num_desired = max(max_num_desired, num_desired)
    if sum_matches % 2 == 1:
        for player, num_desired in max_matches.items():
            if num_desired == max_num_desired:
                max_matches[player] -= 1
                break

    # Make variables
    all_players = list(ratings.keys())
    matchups = dict()
    for p_idx in range(len(all_players)):
        p1_name = all_players[p_idx]
        matchups[p1_name] = dict()
        for q_idx in range(p_idx + 1, len(all_players)):
            p2_name = all_players[q_idx]
            matchups[p1_name][p2_name] = pulp.LpVariable(
                "Matchup_{0}_{1}".format(p1_name, p2_name), 0, 1, pulp.LpInteger
            )

    # Make optimization function
    max_cost = 0
    for val in costs.values():
        max_cost = max(max_cost, val)

    # Add utility value of each matchup
    weighting = dict()
    for player in matchups:
        for opp in matchups[player]:
            weighting[matchups[player][opp]] = get_utility(ratings[player], ratings[opp]) + max_cost

    # Subtract rematchup cost
    for m, cost in costs.items():
        weighting[matchups[m[0]][m[1]]] -= cost

    # Multiply by player-specific cost penalty
    for cost_player, cost_mult in cost_multipliers.items():
        for player in matchups:
            for opp in matchups[player]:
                if player == cost_player or opp == cost_player:
                    weighting[matchups[player][opp]] *= cost_mult

    # Set optimization objective
    prob.setObjective(pulp.LpAffineExpression(weighting, name="Elo weighting"))

    # Make constraints
    for player in matchups:
        edges_from_player = [matchups[player][opp] for opp in matchups[player]]
        for otherplayer in matchups:
            if player in matchups[otherplayer]:
                edges_from_player.append(matchups[otherplayer][player])

        if player in max_matches:
            prob += pulp.lpSum(edges_from_player) <= max_matches[player], ""
        else:
            prob += pulp.lpSum(edges_from_player) <= 1, ""

    prob.solve(pulp.PULP_CBC_CMD(maxSeconds=20, msg=0, fracGap=0.001))
    print("Status:", pulp.LpStatus[prob.status])
    created_matches = []
    for player in matchups:
        for opp in matchups[player]:
            if pulp.value(matchups[player][opp]) == 1:
                created_matches.append((player, opp,))
    return created_matches


# Testing -------------------------------------------------------------------------------------------------

def get_elos():
    elo_str = """
   1 spootybiscuit        678   91   91    49   65%   565    0% 
   2 incnone              655   84   84    60   63%   552    0% 
   3 mudjoe2              620   82   82    60   60%   545    0% 
   4 jackofgames          608  103  103    38   61%   531    0% 
   5 oblivion111          549   91   91    47   53%   526    0% 
   6 cyber_1              490   85   85    59   61%   397    0% 
   7 mayantics            464   89   89    51   39%   545    0% 
   8 naymin               456   82   82    68   65%   328    0% 
   9 staekk               452   84   84    57   44%   501    0% 
  10 paperdoopliss        445  104  104    35   46%   476    0% 
  11 revalize             416   92   92    52   62%   325    0% 
  12 pillarmonkey         406  129  129    24   63%   310    0% 
  13 tufwfo               404   91   91    48   58%   340    0% 
  14 disgruntledgoof      400   91   91    51   61%   314    0% 
  15 echaen               399   89   89    54   43%   455    0% 
  16 squega               390   86   86    51   47%   413    0% 
  17 moyuma               373   92   92    46   50%   370    0% 
  18 fraxtil              368  119  119    27   59%   302    0% 
  19 pancelor             367   98   98    41   59%   305    0% 
  20 tictacfoe            335  126  126    29   72%   160    0% 
  21 necrorebel           315  103  103    37   54%   283    0% 
  22 thedarkfreaack       303  102  102    36   50%   305    0% 
  23 roncli               301  105  105    38   47%   311    0% 
  24 yjalexis             299   95   95    46   52%   274    0% 
  25 paratroopa1          286  108  108    33   45%   320    0% 
  26 abuyazan             262  102  102    37   46%   293    0% 
  27 gunlovers            206  106  106    36   67%    90    0% 
  28 pibonacci            204  142  142    20   60%   137    0% 
  29 invertttt            197  143  143    18   44%   234    0% 
  30 kingtorture          159  108  108    33   58%   112    0% 
  31 slackaholicus        141  113  113    32   50%   145    0% 
  32 bacing               133  127  127    26   42%   185    0% 
  33 grimy42              125  116  116    32   63%    36    0% 
  34 sponskapatrick       124  142  142    21   43%   180    0% 
  35 flygluffet           118  119  119    27   63%    29    0% 
  36 artq                 117  104  104    40   65%     2    0% 
  37 thouther             112  140  140    17   59%    56    0% 
  38 bastet                93  135  135    21   57%    40    0% 
  39 mantasmbl             91  113  113    34   50%    88    0% 
  40 heather               91  128  128    21   52%    76    0% 
  41 progus91              87  113  113    30   50%    91    0% 
  42 sirwuffles            72  107  107    35   54%    39    0% 
  43 gfitty                66  108  108    33   55%    40    0% 
  44 arboretic             65  111  111    33   58%     8    0% 
  45 hordeoftribbles       57  114  114    30   47%    79    0% 
  46 ratata                57  129  129    30   23%   272    0% 
  47 medvezhonok           55  110  110    37   41%   129    0% 
  48 madhyena              22  142  142    24   17%   268    0% 
  49 cs1                   22  110  110    32   47%    48    0% 
  50 yuka                  -9  115  115    37   68%  -149    0% 
  51 emuemu               -18  128  128    24   42%    36    0% 
  52 raviolinguini        -27  104  104    35   46%     1    0% 
  53 spacecow2455         -28  122  122    35   66%  -171    0% 
  54 sailormint           -36  164  164    12   33%    62    0% 
  55 tetel                -45  161  161    20   80%  -271    0% 
  56 teraka               -51  145  145    23   78%  -290    0% 
  57 wonderj13            -58  119  119    27   48%   -47    0% 
  58 flamehaze0           -95  260  260    12    0%   338    0% 
  59 asherrose           -112  116  116    34   47%   -85    0% 
  60 crazyeightsfan69    -127  116  116    30   40%   -53    0% 
  61 axem                -134  114  114    32   50%  -134    0% 
  62 kingcaptain27       -159  119  119    29   66%  -287    0% 
  63 saakas0206          -172  124  124    30   23%    25    0% 
  64 missingno           -183  134  134    30   20%    62    0% 
  65 cheesiestpotato     -188  114  114    33   55%  -223    0% 
  66 boredmai            -236  108  108    36   58%  -296    0% 
  67 ekimekim            -264  132  132    30   20%    -9    0% 
  68 plectro             -275  142  142    18   67%  -388    0% 
  69 kika                -286  110  110    32   53%  -306    0% 
  70 famslayer           -288  122  122    26   54%  -324    0% 
  71 thalen              -292  125  125    27   37%  -192    0% 
  72 hypershock          -296  121  121    29   45%  -248    0% 
  73 yuuchan             -298  115  115    31   61%  -381    0% 
  74 skullgirls          -300  117  117    27   56%  -336    0% 
  75 madoka              -321  131  131    20   55%  -354    0% 
  76 muffin              -329  105  105    32   56%  -368    0% 
  77 zellyff             -332  132  132    26   38%  -243    0% 
  78 greenyoshi          -345  110  110    32   41%  -273    0% 
  79 midna               -347  108  108    33   39%  -272    0% 
  80 odoko_noko          -380  118  118    32   50%  -387    0% 
  81 the_crystal_clod    -385  113  113    34   50%  -386    0% 
  82 amak11              -397  114  114    32   34%  -272    0% 
  83 gauche              -415  122  122    30   40%  -341    0% 
  84 sillypears          -416  116  116    30   47%  -390    0% 
  85 wow_tomato          -445  111  111    32   56%  -494    0% 
  86 definitely_not_him  -462  129  129    24   33%  -341    0% 
  87 zetto               -501  281  281     6    0%  -169    0% 
  88 gemmi               -519  169  169    12   33%  -416    0% 
  89 paperlaur           -526  121  121    30   33%  -405    0% 
  90 uselessgamer        -575  228  228     6   17%  -400    0% 
  91 lismati             -576  139  139    24   21%  -347    0% 
  92 janegland           -632  265  265     6    0%  -346    0% 
  93 cyberman            -742  203  203    24    0%  -292    0% 
  94 tome123             -833  218  218    18    0%  -428    0% 
    """

    the_elos = {}
    for line in elo_str.split('\n'):
        args = line.split()
        if args:
            the_elos[args[1]] = int(args[2])

    return the_elos


def get_winner(elo1, elo2):
    pwin = 1.0 / (1 + pow(10, float(elo2 - elo1)/400.0))
    if rand.random() < pwin:
        return 1
    else:
        return 2


def test_one_matchup():
    def get_p_for_pair(a: float, b: float, eloval: int) -> float:
        return a*(678-eloval)/1511 + b*(eloval + 833)/1511

    pgn_format_str = \
        '[White "{winner}"]\n' \
        '[Black "{loser}"]\n' \
        '[Result "1-0"]\n' \
        '\n' \
        '1-0\n' \
        '\n'

    the_elos = get_elos()

    the_costs = dict()  # type: Dict[Tuple[str, str], float]
    the_cost_multipliers = dict()  # type: Dict[str, float]

    to_delete = []
    for the_player in the_elos:
        if rand.random() > get_p_for_pair(0.3, 1.0, the_elos[the_player]):
            to_delete.append(the_player)
        else:
            the_cost_multipliers[the_player] = 1.0

    for player in to_delete:
        del the_elos[player]

    num_matches = dict()
    for pname in the_elos:
        num_matches[pname] = 2

    week_matches = get_matchups(
        ratings=the_elos,
        max_matches=num_matches,
        costs=the_costs,
        cost_multipliers=the_cost_multipliers
    )

    matchups = dict()   # type: Dict[Tuple[str, str], List[Tuple[int, int]]]
    for i in range(10):
        with open('test{}.pgn'.format(i), 'w') as pgn_file:
            for p1, p2 in week_matches:
                elo1 = the_elos[p1]
                elo2 = the_elos[p2]
                p1_wins = 0
                p2_wins = 0
                for j in range(3):
                    next_winner = get_winner(elo1, elo2)
                    if next_winner == 1:
                        pgn_file.write(pgn_format_str.format(winner=p1, loser=p2))
                        p1_wins += 1
                    else:
                        pgn_file.write(pgn_format_str.format(winner=p2, loser=p1))
                        p2_wins += 1
                if (p1, p2,) in matchups:
                    matchups[(p1, p2,)].append((p1_wins, p2_wins,))
                else:
                    matchups[(p1, p2,)] = [(p1_wins, p2_wins,)]

    with open('matchups.txt', 'w') as matchup_file:
        for players, wins in sorted(matchups.items(), key=lambda x: the_elos[x[0][0]] + the_elos[x[0][1]], reverse=True):
            matchup_str = '{p1:>20} - {p2:<20} '.format(p1=players[0], p2=players[1])
            for pair in wins:
                matchup_str += '[{s1} - {s2}] '.format(s1=pair[0], s2=pair[1])
            matchup_str += '\n'
            matchup_file.write(matchup_str)


def old_main_test():
    def get_p_for_pair(p1: float, p2: float, eloval: int) -> float:
        return p1*(678-eloval)/1511 + p2*(eloval + 833)/1511

    def get_p_for_num(num: int, eloval: int):
        # p_for_nums = [[0.5, 0.95], [0.1, 0.8], [0.1, 0.5]]
        p_for_nums = [[0.05, 0.8], [0.1, 0.4], [0.1, 0.3]]
        num = max(1, min(num, 3))
        num -= 1
        return get_p_for_pair(p_for_nums[num][0], p_for_nums[num][1], eloval)

    def get_num_wanted() -> Dict[str, int]:
        num_wanted = dict()
        for pname, eloval in the_elos.items():
            if rand.random() < get_p_for_num(1, eloval):
                if rand.random() < get_p_for_num(2, eloval):
                    if rand.random() < get_p_for_num(3, eloval):
                        num_wanted[pname] = 3
                    else:
                        num_wanted[pname] = 2
                else:
                    num_wanted[pname] = 1
            else:
                num_wanted[pname] = 0
            num_wanted[pname] = 2
        return num_wanted

    def print_dict_as_csv(matchups_by_player: Dict[str, Dict[int, List[str]]]) -> None:
        outfile = open('ilp_test.txt', 'w')
        for plr, week_dict in matchups_by_player.items():
            the_line = ''
            for week, opps in week_dict.items():
                if week == 0:
                    the_line += plr + ',' + opps[0] + ','
                else:
                    for opp in opps:
                        the_line += opp + ','
                    if len(opps) == 0:
                        the_line += ' , , ,'
                    elif len(opps) == 1:
                        the_line += ' , ,'
                    elif len(opps) == 2:
                        the_line += ' ,'

            the_line = the_line[:-1] + '\n'
            outfile.write(the_line)

    the_elos = get_elos()

    # Trim players
    # player_trim = [0.3, 1]
    # elovals = list(the_elos.items())
    # for the_player, the_elo in elovals:
    #     if rand.random() > get_p_for_pair(player_trim[0], player_trim[1], the_elo):
    #         del the_elos[the_player]

    # Do other stuff
    MATCHUP_PENALTY = 0.97
    NUM_WEEKS = 6
    the_costs = dict()                  # type: Dict[Tuple[str, str], float]
    the_cost_multipliers = dict()       # type: Dict[str, float]
    matches_by_week = []                # type: List[List[Tuple[str,str]]]

    for the_player in the_elos:
        the_cost_multipliers[the_player] = 1.0

    for _ in range(NUM_WEEKS):
        the_num_wanted = get_num_wanted()
        week_matches = get_matchups(
            elos=the_elos,
            max_matches=the_num_wanted,
            costs=the_costs,
            cost_multipliers=the_cost_multipliers
        )
        matches_by_week.append(week_matches)
        for matchup in the_costs:
            the_costs[matchup] *= 0.65

        for matchup in week_matches:
            if matchup in the_costs:
                the_costs[matchup] += 3
            else:
                the_costs[matchup] = 3
            the_cost_multipliers[matchup[0]] *= MATCHUP_PENALTY
            the_cost_multipliers[matchup[1]] *= MATCHUP_PENALTY

        for the_player in the_cost_multipliers.keys():
            the_cost_multipliers[the_player] /= MATCHUP_PENALTY

    matches_by_player = dict()      # type: Dict[str, Dict[int, List[str]]]
    for the_player in the_elos:
        matches_by_player[the_player] = {0: [str(the_elos[the_player])]}
        for i in range(1, NUM_WEEKS + 1):
            matches_by_player[the_player][i] = []

    for i in range(NUM_WEEKS):
        for matchup in matches_by_week[i]:
            p1 = matchup[0]
            p2 = matchup[1]
            matches_by_player[p1][i+1].append(p2)
            matches_by_player[p2][i+1].append(p1)

    print_dict_as_csv(matches_by_player)
    print('Done.')


if __name__ == "__main__":
    test_one_matchup()