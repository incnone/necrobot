import random
import necrobot.exception

rand = random.Random()
rand.seed()


def random_automatch(
        matches_per_entrant: int,
        entrants: list,
        disallowed_matches: list
) -> list:
    """Randomly automatch the entrants, avoiding duplication
    
    Parameters
    ----------
    matches_per_entrant: int
        The number of matches to give each entrant
    entrants: list[int]
        The entrants to match up (by user ID)
    disallowed_matches: list[int, int]
        Matches that are not allowed to be made.

    Returns
    -------
    list[int,int]
        The created matchups.
        
    Raises
    ------
    NoMatchupExistsException
        If it is impossible to satisfy the constraints
    """

