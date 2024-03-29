import asyncio
from necrobot.match.matchinfo import MatchInfo


class League(object):
    """A league, which is a group of matches using the same MatchInfo and possibly recorded to some GSheet.
    
    WARNING: You must call commit() after making changes if you want the changes to be saved to the database.
    """
    def __init__(
            self,
            commit_fn,  # Callable[League, Coroutine[Any]]
            league_tag: str,
            league_name: str,
            match_info: MatchInfo,
            worksheet_id: str = None,
    ):
        self._commit = commit_fn
        self.tag = league_tag
        self.name = league_name
        self.match_info = match_info
        self.worksheet_id = worksheet_id

    def commit(self):
        asyncio.ensure_future(self._commit(self))
