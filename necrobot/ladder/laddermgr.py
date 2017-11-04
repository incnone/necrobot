from typing import Dict

import necrobot.league.the_league
import necrobot.exception

from necrobot.database import leaguedb
from necrobot.util import console
from necrobot.botbase import server
from necrobot.ladder import ratingutil

from necrobot.config import Config
from necrobot.botbase.manager import Manager
from necrobot.necroevent.necroevent import NecroEvent, NEDispatch
from necrobot.util.singleton import Singleton
from necrobot.ladder.rating import Rating


class LadderMgr(Manager, metaclass=Singleton):
    """Manager object for the global League, if any."""

    def __init__(self):
        self._main_channel = None
        self._notifications_channel = None
        self._schedule_channel = None
        self._client = None
        NEDispatch().subscribe(self)

    @property
    def league(self):
        return necrobot.league.the_league.league

    async def initialize(self):
        self._main_channel = server.main_channel
        self._notifications_channel = server.find_channel(channel_name=Config.NOTIFICATIONS_CHANNEL_NAME)
        self._client = server.client

    async def refresh(self):
        self._notifications_channel = server.find_channel(channel_name=Config.NOTIFICATIONS_CHANNEL_NAME)
        self._client = server.client

    async def close(self):
        pass

    def on_botchannel_create(self, channel, bot_channel):
        pass

    async def ne_process(self, ev: NecroEvent):
        if ev.event_type == 'end_match':
            racer_1 = ev.match.racer_1
            racer_2 = ev.match.racer_2
            r1_old = await leaguedb.get_rating(racer_1.user_id)
            r2_old = await leaguedb.get_rating(racer_2.user_id)

            new_ratings = await ratingutil.compute_ratings()  # type: Dict[int, Rating]
            await leaguedb.set_ratings(new_ratings)

            r1_new = new_ratings[racer_1.user_id]
            r2_new = new_ratings[racer_2.user_id]

            await server.client.send_message(
                self._main_channel,
                'Match complete: **{r1}** [{w1}-{w2}] **{r2}** :tada:\n'
                '**{r1}**: {r1_old} => {r1_new}\n'
                '**{r2}**: {r2_old} => {r2_new}\n'.format(
                    r1=ev.match.racer_1.display_name,
                    r2=ev.match.racer_2.display_name,
                    w1=ev.r1_wins,
                    w2=ev.r2_wins,
                    r1_old=r1_old.displayed_rating,
                    r2_old=r2_old.displayed_rating,
                    r1_new=r1_new.displayed_rating,
                    r2_new=r2_new.displayed_rating
                )
            )

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
