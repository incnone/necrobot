import random

MIN_SEED = 1            
MAX_SEED = 99999999


def init_seed():
    random.seed()


def get_new_seed():
    return random.randint(MIN_SEED, MAX_SEED)
