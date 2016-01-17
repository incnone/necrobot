## Holds permission data for a private race room

from enum import Enum

MatchType = {'single':0,'bestof':1,'repeat':2}
  
class MatchInfo(object):
    match_type = MatchType['single']
    bestof = 0
    repeat = 0
