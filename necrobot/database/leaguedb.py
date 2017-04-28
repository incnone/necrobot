"""
Interaction with the necrobot.leagues table.

Methods
-------
create_league(schema_name: str) -> None
    Make a new league.
get_league(schema_name: str) -> League
    Get a registered league.
get_entrant_ids() -> list[int]
    Get the NecroUser IDs of all entrants.
register_user(user_id: int) -> None
    Register a user in the `entrants` table.
write_league(League) -> None
    Write information in an already registered league to the database.

Exceptions
----------
LeagueAlreadyExists
LeagueDoesNotExist
InvalidSchemaName
"""

import re
import necrobot.exception

from necrobot.config import Config
from necrobot.database import racedb
from necrobot.database.dbconnect import DBConnect
from necrobot.database.dbutil import tn
from necrobot.league.league import League
from necrobot.match.matchinfo import MatchInfo
from necrobot.race.raceinfo import RaceInfo


async def create_league(schema_name: str) -> League:
    """Creates a new CoNDOR event with the given schema_name as its database.
    
    Parameters
    ----------
    schema_name: str
        The name of the database schema for this event, and also the unique identifier for this event.

    Raises
    ------
    LeagueAlreadyExists
        When the schema_name already exists.
    """
    table_name_validator = re.compile(r'^[0-9a-zA-Z_$]+$')
    if not table_name_validator.match(schema_name):
        raise necrobot.exception.InvalidSchemaName()

    params = (schema_name,)
    async with DBConnect(commit=True) as cursor:
        cursor.execute(
            """
            SELECT `league_name` 
            FROM `leagues` 
            WHERE `schema_name`=%s
            """,
            params
        )
        for row in cursor:
            raise necrobot.exception.LeagueAlreadyExists(row[0])

        cursor.execute(
            """
            SELECT SCHEMA_NAME 
            FROM INFORMATION_SCHEMA.SCHEMATA 
            WHERE SCHEMA_NAME = %s
            """,
            params
        )
        for _ in cursor:
            raise necrobot.exception.LeagueAlreadyExists('Schema exists, but is not a CoNDOR event.')

        cursor.execute(
            """
            CREATE SCHEMA `{schema_name}` 
            DEFAULT CHARACTER SET = utf8 
            DEFAULT COLLATE = utf8_general_ci
            """.format(schema_name=schema_name)
        )
        cursor.execute(
            """
            INSERT INTO `leagues` 
            (`schema_name`) 
            VALUES (%s)
            """,
            params
        )

        cursor.execute(
            """
            CREATE TABLE `{schema_name}`.`entrants` (
                `user_id` smallint unsigned NOT NULL,
                PRIMARY KEY (`user_id`)
            ) DEFAULT CHARSET=utf8
            """.format(schema_name=schema_name)
        )

        for tablename in ['matches', 'match_races', 'races', 'race_runs']:
            cursor.execute(
                "CREATE TABLE `{league_schema}`.`{table}` LIKE `{necrobot_schema}`.`{table}`".format(
                    league_schema=schema_name,
                    necrobot_schema=Config.MYSQL_DB_NAME,
                    table=tablename
                )
            )

    return League(
        commit_fn=write_league,
        schema_name=schema_name,
        league_name='<unnamed league>',
        match_info=MatchInfo()
    )


async def get_entrant_ids() -> list:
    """Get NecroUser IDs for all entrants to the league
    
    Returns
    -------
    list[int]
    """
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT `user_id`
            FROM {entrants}
            """.format(entrants=tn('entrants'))
        )
        to_return = []
        for row in cursor:
            to_return.append(int(row[0]))
        return to_return


async def get_league(schema_name: str) -> League:
    """
    Parameters
    ----------
    schema_name: str
        The name of the schema for the event (and also the event's unique identifier).

    Returns
    -------
    League
        A League object for the event.
    """
    params = (schema_name,)
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT 
               `leagues`.`league_name`, 
               `leagues`.`number_of_races`, 
               `leagues`.`is_best_of`, 
               `leagues`.`ranked`, 
               `leagues`.`gsheet_id`,
               `leagues`.`deadline`,
               `race_types`.`character`, 
               `race_types`.`descriptor`, 
               `race_types`.`seeded`, 
               `race_types`.`amplified`, 
               `race_types`.`seed_fixed` 
            FROM `leagues` 
            LEFT JOIN `race_types` ON `leagues`.`race_type` = `race_types`.`type_id` 
            WHERE `leagues`.`schema_name` = %s 
            LIMIT 1
            """,
            params
        )
        for row in cursor:
            race_info = RaceInfo()
            if row[6] is not None:
                race_info.set_char(row[6])
            if row[7] is not None:
                race_info.descriptor = row[7]
            if row[8] is not None:
                race_info.seeded = bool(row[8])
            if row[9] is not None:
                race_info.amplified = bool(row[9])
            if row[10] is not None:
                race_info.seed_fixed = bool(row[10])

            match_info = MatchInfo(
                max_races=int(row[1]) if row[1] is not None else None,
                is_best_of=bool(row[2]) if row[2] is not None else None,
                ranked=bool(row[3]) if row[3] is not None else None,
                race_info=race_info
            )

            return League(
                commit_fn=write_league,
                schema_name=schema_name,
                league_name=row[0],
                match_info=match_info,
                gsheet_id=row[4],
                deadline=row[5]
            )

        raise necrobot.exception.LeagueDoesNotExist()


async def register_user(user_id: int) -> None:
    """Register the user for the league
    
    Parameters
    ----------
    user_id: int
        The user's NecroUser ID.
    """
    async with DBConnect(commit=True) as cursor:
        params = (user_id,)
        cursor.execute(
            """
            INSERT INTO {entrants}
                (user_id)
            VALUES (%s)
            ON DUPLICATE KEY UPDATE
                user_id = VALUES(user_id)
            """.format(entrants=tn('entrants')),
            params
        )


async def write_league(league: League) -> None:
    """Write the league to the database
    
    Parameters
    ----------
    league: League
        The league object to be written. Will create a new row if the schema_name is not in the database, and
        update otherwise.
    """
    match_info = league.match_info
    race_type_id = await racedb.get_race_type_id(race_info=match_info.race_info, register=True)

    async with DBConnect(commit=True) as cursor:
        params = (
            league.schema_name,
            league.name,
            league.gsheet_id,
            league.deadline,
            match_info.max_races,
            match_info.is_best_of,
            match_info.ranked,
            race_type_id,
        )

        cursor.execute(
            """
            INSERT INTO `leagues` 
            (
                `schema_name`, 
                `league_name`, 
                `gsheet_id`, 
                `deadline`, 
                `number_of_races`, 
                `is_best_of`, 
                `ranked`, 
                `race_type`
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE
               `league_name` = VALUES(`league_name`), 
               `gsheet_id` = VALUES(`gsheet_id`),
               `deadline` = VALUES(`deadline`),
               `number_of_races` = VALUES(`number_of_races`), 
               `is_best_of` = VALUES(`is_best_of`), 
               `ranked` = VALUES(`ranked`), 
               `race_type` = VALUES(`race_type`)
            """,
            params
        )
