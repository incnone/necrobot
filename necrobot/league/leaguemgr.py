import datetime
import functools
from typing import Optional

import necrobot.exception
from necrobot.league import leaguedb
from necrobot.botbase.manager import Manager
from necrobot.config import Config
from necrobot.database import dbutil
from necrobot.util import console
from necrobot.util.parse import dateparse
from necrobot.util.singleton import Singleton
from necrobot.match.matchglobals import MatchGlobals


class LeagueMgr(Manager, metaclass=Singleton):
    _the_league = None

    """Manager object for the global League, if any."""
    def __init__(self):
        pass

    @property
    def league(self):
        return self._the_league

    async def initialize(self):
        if Config.LEAGUE_NAME:
            try:
                await self.set_league(schema_name=Config.LEAGUE_NAME, save_to_config=False)
            except necrobot.exception.LeagueDoesNotExist:
                console.warning(
                    'League "{0}" does not exist.'.format(Config.LEAGUE_NAME)
                )

    async def refresh(self):
        pass

    async def close(self):
        pass

    def on_botchannel_create(self, channel, bot_channel):
        pass

    @classmethod
    async def create_league(cls, schema_name: str, save_to_config=True):
        """Registers a new league
        
        Parameters
        ----------
        schema_name: str
            The schema name for the league
        save_to_config: bool
            Whether to make this the default league, i.e., save the schema name to the bot's config file
    
        Raises
        ------
        necrobot.database.leaguedb.LeagueAlreadyExists
            If the schema name refers to a registered league
        necrobot.database.leaguedb.InvalidSchemaName
            If the schema name is not a valid MySQL schema name
        """
        cls._the_league = await leaguedb.create_league(schema_name)
        dbutil.league_schema_name = schema_name

        if save_to_config:
            Config.LEAGUE_NAME = schema_name
            Config.write()

    @classmethod
    async def set_league(cls, schema_name: str, save_to_config=True):
        """Set the current league
        
        Parameters
        ----------
        schema_name: str
            The schema name for the league
        save_to_config: bool
            Whether to make this the default league, i.e., save the schema name to the bot's config file
    
        Raises
        ------
        necrobot.database.leaguedb.LeagueDoesNotExist
            If the schema name does not refer to a registered league
        """
        cls._the_league = await leaguedb.get_league(schema_name)
        dbutil.league_schema_name = schema_name

        MatchGlobals().set_deadline_fn(LeagueMgr.deadline)

        if save_to_config:
            Config.LEAGUE_NAME = schema_name
            Config.write()

    @staticmethod
    def deadline() -> Optional[datetime.datetime]:
        if LeagueMgr._the_league is not None:
            deadline_str = LeagueMgr._the_league.deadline
            if deadline_str is not None:
                return dateparse.parse_datetime(deadline_str)
        return None
