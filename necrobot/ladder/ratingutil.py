from math import sqrt, erf
from typing import List, Dict, Tuple

from necrobot.util import console
from necrobot.database import racedb

from necrobot.ladder.rating import Rating
from whr.base.base import WholeHistoryRating


RATINGS_GLOBAL_OFFSET = 1600
PARAM_W = 13
PARAM_PRIOR_STDEV = 400.0
PARAM_ITERATE_ELO_DIFF = 0.1
PARAM_ITERATE_MAX_CYCLES = 500


async def compute_ratings() -> Dict[int, Rating]:
    game_data = await racedb.get_game_data_for_ratings()
    return _compute_ratings_hlpr(game_data)


def _compute_ratings_hlpr(raw_game_data: List[Tuple]) -> Dict[int, Rating]:
    """Compute the WHR from the given game data.
    
    Parameters
    ----------
    raw_game_data: List[Tuple]
        A list of triples of the form (winner_id, loser_id, timestamp) representing the games to compute ratings from.

    Returns
    -------
    Dict[int, Rating]
        A map from user_ids to computed Ratings.
    """

    # Create set of all players
    player_ids = set()

    # Make a WHR object
    the_whr = WholeHistoryRating(verbose=False, w=PARAM_W, prior_stdev=PARAM_PRIOR_STDEV)

    # Add games to the WHR object
    for game in raw_game_data:
        # Add IDs to our set
        player_ids.add(game[0])
        player_ids.add(game[1])

        # Compute the time step for this game
        time_step = 0

        # Add the game to the WHR object
        the_whr.create_game(black=str(game[0]), white=str(game[1]), winner='B', time_step=time_step)

    # Compute the elos
    the_whr.iterate_until(elo_diff=PARAM_ITERATE_ELO_DIFF, max_cycles=PARAM_ITERATE_MAX_CYCLES)

    # Put ratings in a dictionary
    ratings = dict()
    for player_id in player_ids:
        ratings_for_player = the_whr.ratings_for_player(str(player_id))
        last_rating = ratings_for_player[len(ratings_for_player) - 1]
        ratings[player_id] = Rating(mu=last_rating[1] + RATINGS_GLOBAL_OFFSET, sigma=last_rating[2])

    return ratings
