from necrobot.database import leaguedb
from necrobot.database import matchdb


MATCHUP_PENALTY = 0.97
COST_MULTIPLIER_NUM_WEEKS = 6


async def get_cost_multiplier(player_id : int) -> float:
    """Gets a multiplicative cost for the player. This is determined by (0.97)^(m-w), where w
    is COST_MULTIPLIER_NUM_WEEKS, and m is the number of matchups that player has played in the last
    w weeks."""
    # TODO
    return 1.0


async def get_cost(player_1_id: int, player_2_id: int) -> float:
    """Gets an additive cost for the matchup. This is determined as 3*(0.65)^w, where
    w is the number of weeks since the last time the matchup has happened."""
    # TODO
    return 0.0


