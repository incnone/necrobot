class Match(object):
    def __init__(self, match_id, *racers):
        self._match_id = match_id           # int -- the unique ID for this match

        # List of all racers in the match
        self._racers = []                   # List of NecroUser objects
        for racer in racers:
            self._racers.append(racer)

        # Scheduling data
        self._suggested_time = None         # datetime.datetime with pytz info attached
        self._confirmed_by = []             # Sublist of self._racers
        self._wishes_to_unconfirm = []      # Sublist of self._racers

        # Format data
        self._number_of_races = None        # Maximum number of races
        self._is_best_of = False            # If true, end match after one player has clinched the most wins

    def __eq__(self, other):
        return self.match_id == other.match_id

    @property
    def match_id(self):
        return self._match_id

    @property
    def racers(self):
        return self._racers

    @property
    def suggested_time(self):
        return self._suggested_time

    @property
    def is_scheduled(self):
        for racer in self.racers:
            if racer not in self._confirmed_by:
                return False
        return True

    @property
    def is_best_of(self):
        return self._is_best_of
