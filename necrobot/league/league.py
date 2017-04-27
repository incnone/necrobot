import asyncio
import types
from necrobot.match.matchinfo import MatchInfo


class League(object):
    """A league, which is a group of matches and/or races all stored in a common database.
    
    Current policy is that there can only be a single active league. Therefore, it should not be necessary to construct 
    these manually; use LeagueManager to get the currently active league.
    
    WARNING: You must call commit() after making changes if you want the changes to be saved to the database.
    """
    def __init__(
            self,
            commit_fn: types.FunctionType,
            schema_name: str,
            league_name: str,
            match_info: MatchInfo,
            gsheet_id: str = None
    ):
        self._commit = commit_fn
        self._schema_name = schema_name
        self.name = league_name
        self.match_info = match_info
        self.gsheet_id = gsheet_id

    @property
    def schema_name(self):
        return self._schema_name

    def commit(self):
        asyncio.ensure_future(self._commit(self))
