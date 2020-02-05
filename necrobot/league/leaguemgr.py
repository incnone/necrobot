from typing import Optional

import necrobot.exception
from necrobot.botbase.manager import Manager
from necrobot.league.league import League
from necrobot.league import leaguedb
from necrobot.match.matchinfo import MatchInfo
from necrobot.util.singleton import Singleton


class LeagueMgr(Manager, metaclass=Singleton):
    _league_lib = dict()

    """Manager object for the global League, if any."""
    def __init__(self):
        pass

    async def initialize(self):
        await self._recover_leagues()

    async def refresh(self):
        pass

    async def close(self):
        pass

    def on_botchannel_create(self, channel, bot_channel):
        pass

    @classmethod
    async def make_league(
            cls,
            league_tag: str,
            league_name: str,
            match_info: Optional[MatchInfo] = None,
            gsheet_id: str = None
    ) -> League:
        # noinspection PyIncorrectDocstring
        """Registers a new league
        
        Parameters
        ----------
        league_tag: str
            A unique tag for the league, used for commands (e.g. "coh")
        league_name: str
            The name of the league (e.g. "Cadence of Hyrule Story Mode"
        match_info: MatchInfo
            The default MatchInfo for a match in this league
        gsheet_id: str
            The GSheet ID of the standings sheet for this league

        Raises
        ------
        LeagueAlreadyExists: If the league tag is already registered to a league
        """

        if league_tag in cls._league_lib:
            raise necrobot.exception.LeagueAlreadyExists()

        if match_info is None:
            match_info = MatchInfo()

        league = League(
            commit_fn=leaguedb.write_league,
            league_tag=league_tag,
            league_name=league_name,
            match_info=match_info,
            gsheet_id=gsheet_id
        )
        league.commit()
        cls._league_lib[league_tag] = league
        return league

    @classmethod
    async def get_league(cls, league_tag: str) -> League:
        """Registers a new league

        Parameters
        ----------
        league_tag: str
            The unique tag for the league

        Raises
        ------
        LeagueDoesNotExist: If the league tag is already registered to a league
        """
        if league_tag in cls._league_lib:
            return cls._league_lib[league_tag]

        return await leaguedb.get_league(league_tag)

    @classmethod
    async def assign_match_to_league(cls, match_id: int, league_tag: str):
        # Check that it's a valid league
        await cls.get_league(league_tag)

        await leaguedb.assign_match(match_id, league_tag)

    async def _recover_leagues(self):
        self._league_lib = dict()
        for league in await leaguedb.get_all_leagues():
            self._league_lib[league.tag] = league
