## Holds permission data for a private race room

from enum import Enum

MatchType = {'single':0,'bestof':1,'repeat':2}
  
class MatchInfo(object):

    def __init__(self):
        self.match_type = MatchType['single']
        self.bestof = 0
        self.repeat = 0
