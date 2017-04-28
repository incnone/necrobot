import necrobot.league.the_league
import necrobot.exception

from necrobot.database import leaguedb
from necrobot.util import console

from necrobot.config import Config
from necrobot.util.singleton import Singleton


class LeagueMgr(object, metaclass=Singleton):
    """Manager object for the global League, if any."""
    def __init__(self):
        pass

    @property
    def league(self):
        return necrobot.league.the_league.league

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

    @staticmethod
    async def create_league(schema_name: str, save_to_config=True):
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
        necrobot.league.the_league.league = await leaguedb.create_league(schema_name)

        if save_to_config:
            Config.LEAGUE_NAME = schema_name
            Config.write()

    @staticmethod
    async def set_league(schema_name: str, save_to_config=True):
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
        necrobot.league.the_league.league = await leaguedb.get_league(schema_name)

        if save_to_config:
            Config.LEAGUE_NAME = schema_name
            Config.write()
