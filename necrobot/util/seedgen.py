import random

MIN_SEED = 1            
MAX_SEED = 16777216     #currently 2^24 as this is the maximum unrounded seed

def init_seed():
    random.seed()

def get_new_seed():
    return random.randint(MIN_SEED, MAX_SEED)
