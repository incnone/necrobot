import math
import pulp
import pulp.solvers
import random
import unittest
from typing import Dict, List, FrozenSet

from necrobot.util import console
from necrobot.ladder import ratingutil

from necrobot.ladder.rating import Rating

MATCHUP_PENALTY = 0.97          # A penalty to matchup utility for each matchup after the first played in a given week
REMATCH_COST_BASE = 3           # The penalty (utils) for a rematch the week after a given match
REMATCH_COST_MULTIPLIER = 0.65  # The reduction per week in penalty for rematches


class RacerAutomatchData(object):
    def __init__(self, rating: Rating, max_matches: int):
        self.rating = rating            # type: Rating
        self.max_matches = max_matches  # type: int
        self.cost_multiplier = 1.0      # type: float


Matchup = FrozenSet[int]
MatchupCosts = Dict[Matchup, float]


def get_matchups(
    automatch_data: Dict[int, RacerAutomatchData],
    past_matches: Dict[int, List[Matchup]]
) -> List[Matchup]:
    matchup_costs = dict()
    fill_costs(matchup_costs=matchup_costs, automatch_data=automatch_data, past_matches=past_matches)
    return get_matchups_helpfn(automatch_data=automatch_data, matchup_costs=matchup_costs)


def fill_costs(
        matchup_costs: MatchupCosts,
        automatch_data: Dict[int, RacerAutomatchData],
        past_matches: Dict[int, List[Matchup]]
) -> None:
    past_matches_items = sorted(past_matches.items(), key=lambda k: k[0])
    last_week = None
    for week, match_list in past_matches_items:
        if last_week is not None:
            week_diff = week - last_week
            for match in matchup_costs:
                matchup_costs[match] *= math.pow(REMATCH_COST_MULTIPLIER, week_diff)

            for pid in automatch_data:
                automatch_data[pid].cost_multiplier /= math.pow(REMATCH_COST_BASE, week_diff)
        last_week = week

        for match in match_list:
            if match in matchup_costs:
                matchup_costs[match] += REMATCH_COST_BASE
            else:
                matchup_costs[match] = REMATCH_COST_BASE

            for pid in match:
                automatch_data[pid].cost_multiplier *= REMATCH_COST_BASE


def get_utility(data_1: RacerAutomatchData, data_2: RacerAutomatchData, cost: float) -> float:
    base_utility = math.sqrt(ratingutil.get_entropy(data_1.rating, data_2.rating))
    return (base_utility - cost)*data_1.cost_multiplier*data_2.cost_multiplier


def get_matchups_helpfn(automatch_data: Dict[int, RacerAutomatchData], matchup_costs: MatchupCosts)-> List[Matchup]:
    if len(automatch_data) == 0:
        console.warning('Tried to make automatches with an empty dict.')
        return list()
    
    # TODO turn off writing to file
    prob = pulp.LpProblem("Matchup problem", pulp.LpMaximize)

    # Pre-optimize by forcing max_matches to have an even sum, by removing a match from the player with the max
    # matches and the smallest cost_multiplier (this significantly speeds up the ILP solve)
    sum_matches = 0
    max_num_desired = 0
    for player, data in automatch_data.items():
        sum_matches += data.max_matches
        max_num_desired = max(max_num_desired, data.max_matches)
    
    if sum_matches % 2 == 1:
        players_to_consider = []
        for player, data in automatch_data.items():
            if data.max_matches == max_num_desired:
                players_to_consider.append(player)
        players_to_consider = sorted(players_to_consider, key=lambda p: automatch_data[p].cost_multiplier)
        automatch_data[players_to_consider[0]].max_matches -= 1

    # Make variables
    players = list(automatch_data.keys())
    matchup_vars = dict()                           # type: Dict[int, Dict[int, pulp.LpVariable]]
    for p_idx in range(len(players)):
        pid = players[p_idx]
        matchup_vars[pid] = dict()                  # type: Dict[int, pulp.LpVariable]
        for q_idx in range(p_idx + 1, len(players)):
            qid = players[q_idx]
            matchup_vars[pid][qid] = pulp.LpVariable("m_{0}_{1}".format(pid, qid), 0, 1, pulp.LpInteger)

    # Make optimization function
    max_cost = 0
    for val in matchup_costs.values():
        max_cost = max(max_cost, val)

    # Store utility values of each matchup
    utility = dict()                                # type: Dict[pulp.LpVariable, float]
    for player in matchup_vars:
        for opp in matchup_vars[player]:
            match_cost = matchup_costs[frozenset([player, opp])] if frozenset([player, opp]) in matchup_costs else 0
            utility[matchup_vars[player][opp]] = get_utility(
                data_1=automatch_data[player],
                data_2=automatch_data[opp],
                cost=match_cost - max_cost
            )

    # Set optimization objective
    prob.setObjective(pulp.LpAffineExpression(utility, name="Matchup Utility"))

    # Make constraints
    for player in matchup_vars:
        edges_from_player = [matchup_vars[player][opp] for opp in matchup_vars[player]]
        for otherplayer in matchup_vars:
            if player in matchup_vars[otherplayer]:
                edges_from_player.append(matchup_vars[otherplayer][player])

        prob += pulp.lpSum(edges_from_player) <= automatch_data[player].max_matches, ""

    # Solve the ILP problem
    solver = pulp.PULP_CBC_CMD(maxSeconds=20, msg=0, keepFiles=0, fracGap=0.001)
    solver.tmpDir = 'tmp'
    prob.solve(solver=solver)
    console.info("ILP problem status: {0}".format(pulp.LpStatus[prob.status]))

    # Get the matches
    created_matches = list()                 # type: List[Matchup]
    for player in matchup_vars:
        for opp in matchup_vars[player]:
            if pulp.value(matchup_vars[player][opp]) == 1:
                created_matches.append(frozenset([player, opp]))
    return created_matches


class TestUtilityMatch(unittest.TestCase):
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

    # Init global vars
    ratings = dict()                    # type: Dict[int, Rating]
    id_translate = {}                   # type: Dict[int, str]
    for line in elo_str.split('\n'):
        args = line.split()
        if args:
            ratings[int(args[0])] = ratingutil.create_rating(mu=float(args[2]), sigma=float(args[3]) / 2)
            id_translate[int(args[0])] = args[1]

    rand = random.Random()
    rand.seed()

    @staticmethod
    def get_p_for_pair(p1: float, p2: float, eloval: int) -> float:
        return p1*(678-eloval)/1511 + p2*(eloval + 833)/1511

    @classmethod
    def get_p_for_num(cls, num: int, eloval: int):
        p_for_nums = [[0.5, 0.95], [0.1, 0.8], [0.1, 0.5]]
        # p_for_nums = [[0.05, 0.8], [0.1, 0.4], [0.1, 0.3]]
        num = max(1, min(num, 3))
        num -= 1
        return cls.get_p_for_pair(p_for_nums[num][0], p_for_nums[num][1], eloval)

    @classmethod
    def get_num_wanted(cls) -> Dict[int, int]:
        num_wanted = dict()
        for pname, eloval in cls.ratings.items():
            if cls.rand.random() < cls.get_p_for_num(1, eloval.mu):
                if cls.rand.random() < cls.get_p_for_num(2, eloval.mu):
                    if cls.rand.random() < cls.get_p_for_num(3, eloval.mu):
                        num_wanted[pname] = 3
                    else:
                        num_wanted[pname] = 2
                else:
                    num_wanted[pname] = 1
            else:
                num_wanted[pname] = 0
        return num_wanted

    @classmethod
    def print_dict_as_csv(cls, matchups_by_player: Dict[int, Dict[int, List[int]]]) -> None:
        with open('ilp_test.txt', 'w') as outfile:
            for plr, week_dict in matchups_by_player.items():
                the_line = ''
                for week, opps in week_dict.items():
                    if week == 0:
                        the_line += cls.id_translate[plr] + ',' + str(opps[0]) + ','
                    else:
                        for opp in opps:
                            the_line += cls.id_translate[opp] + ','
                        if len(opps) == 0:
                            the_line += ' , , ,'
                        elif len(opps) == 1:
                            the_line += ' , ,'
                        elif len(opps) == 2:
                            the_line += ' ,'

                the_line = the_line[:-1] + '\n'
                outfile.write(the_line)

    def test_utility_match(self):
        # Trim players
        # player_trim = [0.3, 1]
        # elovals = list(the_elos.items())
        # for the_player, the_elo in elovals:
        #     if rand.random() > get_p_for_pair(player_trim[0], player_trim[1], the_elo):
        #         del the_elos[the_player]

        # Get the matchups
        num_weeks = 16
        matches_by_week = dict()                # type: Dict[int, List[Matchup]]

        for week in range(1, num_weeks+1):
            the_num_wanted = self.get_num_wanted()
            automatch_data = dict()             # type: Dict[int, RacerAutomatchData]()
            for user_id, user_rating in self.ratings.items():
                automatch_data[user_id] = RacerAutomatchData(rating=user_rating, max_matches=the_num_wanted[user_id])

            try:
                matches_by_week[week] = get_matchups(
                    automatch_data=automatch_data,
                    past_matches=matches_by_week
                )
            except pulp.solvers.PulpSolverError:
                print('SolverError oh no.')
                return

        # Sort our matches by player and week for easy viewing
        matches_by_player = dict()              # type: Dict[int, Dict[int, List[int]]]
        for player_id in self.ratings:
            matches_by_player[player_id] = {0: [int(self.ratings[player_id].mu)]}
            for week in range(1, num_weeks + 1):
                matches_by_player[player_id][week] = []

        for week in range(1, num_weeks + 1):
            for matchup in matches_by_week[week]:
                plist = list(matchup)
                p1 = plist[0]
                p2 = plist[1]
                matches_by_player[p1][week].append(p2)
                matches_by_player[p2][week].append(p1)

        self.print_dict_as_csv(matches_by_player)
