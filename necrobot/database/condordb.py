"""
Interaction with the necrobot.condor_events table.
"""

import re
from necrobot.database import racedb

from necrobot.config import Config
from necrobot.database.dbconnect import DBConnect
from necrobot.match.matchinfo import MatchInfo
from necrobot.race.raceinfo import RaceInfo


class EventAlreadyExists(Exception):
    def __init__(self, exc_str=None):
        self._exc_str = exc_str

    def __str__(self):
        return self._exc_str if self._exc_str is not None else ''


class EventDoesNotExist(Exception):
    pass


class InvalidSchemaName(Exception):
    pass


def create_new_event(schema_name: str):
    """Creates a new CoNDOR event with the given schema_name as its database.
    
    Parameters
    ----------
    schema_name: str
        The name of the database schema for this event, and also the unique identifier for this event.

    Raises
    ------
    EventAlreadyExists
        When the schema_name already exists.
    """
    table_name_validator = re.compile(r'^[0-9a-zA-Z_$]+$')
    if not table_name_validator.match(schema_name):
        raise InvalidSchemaName()

    params = (schema_name,)
    with DBConnect(commit=True) as cursor:
        cursor.execute(
            "SELECT `event_name` "
            "FROM `condor_events` "
            "WHERE `schema_name`=%s ",
            params
        )
        for row in cursor:
            raise EventAlreadyExists(row[0])

        cursor.execute(
            "SELECT SCHEMA_NAME "
            "FROM INFORMATION_SCHEMA.SCHEMATA "
            "WHERE SCHEMA_NAME = %s",
            params
        )
        for _ in cursor:
            raise EventAlreadyExists('Schema exists, but is not a CoNDOR event.')

        cursor.execute(
            "CREATE SCHEMA `{0}` "
            "DEFAULT CHARACTER SET = utf8 "
            "DEFAULT COLLATE = utf8_general_ci".format(schema_name)
        )
        cursor.execute(
            "INSERT INTO `condor_events` "
            "(`schema_name`) "
            "VALUES (%s)",
            params
        )

        cursor.execute(
            "CREATE TABLE `{0}`.`matches` LIKE `{1}`.`matches`".format(schema_name, Config.MYSQL_DB_NAME))
        cursor.execute(
            "CREATE TABLE `{0}`.`match_races` LIKE `{1}`.`match_races`".format(schema_name, Config.MYSQL_DB_NAME))
        cursor.execute(
            "CREATE TABLE `{0}`.`races` LIKE `{1}`.`races`".format(schema_name, Config.MYSQL_DB_NAME))
        cursor.execute(
            "CREATE TABLE `{0}`.`race_runs` LIKE `{1}`.`race_runs`".format(schema_name, Config.MYSQL_DB_NAME))


def get_event_match_info(schema_name: str) -> MatchInfo:
    """
    Parameters
    ----------
    schema_name: str
        The name of the schema for the event (and also the event's unique identifier).
    
    Returns
    -------
    MatchInfo
        The default MatchInfo for the event.
    """
    params = (schema_name,)
    with DBConnect(commit=False) as cursor:
        cursor.execute(
            "SELECT "
            "   `condor_events`.`number_of_races`, "
            "   `condor_events`.`is_best_of`, "
            "   `condor_events`.`ranked`, "
            "   `race_types`.`character`, "
            "   `race_types`.`descriptor`, "
            "   `race_types`.`seeded`, "
            "   `race_types`.`amplified`, "
            "   `race_types`.`seed_fixed` "
            "FROM `condor_events` "
            "LEFT JOIN `race_types` ON `condor_events`.`race_type` = `race_types`.`type_id` "
            "WHERE `condor_events`.`schema_name` = %s",
            params
        )
        for row in cursor:
            race_info = RaceInfo()
            if row[3] is not None:
                race_info.set_char(row[3])
            if row[4] is not None:
                race_info.descriptor = row[4]
            if row[5] is not None:
                race_info.seeded = bool(row[5])
            if row[6] is not None:
                race_info.amplified = bool(row[6])
            if row[7] is not None:
                race_info.seed_fixed = bool(row[7])

            match_info = MatchInfo(
                max_races=int(row[0]) if row[0] is not None else None,
                is_best_of=bool(row[1]) if row[1] is not None else None,
                ranked=bool(row[2]) if row[2] is not None else None,
                race_info=race_info
            )
            return match_info

        raise EventDoesNotExist()


def get_event_name(schema_name: str) -> str:
    """
    Parameters
    ----------
    schema_name: str
        The name of the schema for the event (and also the event's unique identifier).
    
    Returns
    -------
    str
        The event's name.
    
    Raises
    ------
    EventDoesNotExist
        When there is no registered event by the given name.
    """
    params = (schema_name,)
    with DBConnect(commit=False) as cursor:
        cursor.execute(
            "SELECT `event_name` "
            "FROM `condor_events` "
            "WHERE `schema_name`=%s",
            params
        )
        event_name_row = cursor.fetchone()
        if event_name_row is None:
            raise EventDoesNotExist()

        cursor.execute(
            "SELECT SCHEMA_NAME "
            "FROM INFORMATION_SCHEMA.SCHEMATA "
            "WHERE SCHEMA_NAME = %s",
            params
        )
        if cursor.fetchone() is None:
            raise EventDoesNotExist()

        return event_name_row[0]


def set_event_match_info(schema_name: str, match_info: MatchInfo):
    """Set the default match info for the given event.
    
    Parameters
    ----------
    schema_name: str
        The name of the schema for the event (and also the event's unique identifier).
    match_info
        The new default MatchInfo.
    """
    with DBConnect(commit=True) as cursor:
        race_type_id = racedb.get_race_type_id(race_info=match_info.race_info, register=True)

        params = (
            match_info.max_races,
            match_info.is_best_of,
            match_info.ranked,
            race_type_id,
            schema_name
        )

        cursor.execute(
            "UPDATE `condor_events` "
            "SET "
            "   `number_of_races`=%s, "
            "   `is_best_of`=%s, "
            "   `ranked`=%s, "
            "   `race_type`=%s "
            "WHERE `schema_name`=%s",
            params
        )


def set_event_name(schema_name: str, event_name: str) -> None:
    """
    Parameters
    ----------
    schema_name: str
        The name of the schema for the event (and also the event's unique identifier).
    event_name: str
        The custom descriptor for the event.    

    Raises
    ------
    EventDoesNotExist
        When there is no registered schema by the given name.
    """
    params = (event_name, schema_name,)
    with DBConnect(commit=True) as cursor:
        cursor.execute(
            "UPDATE `condor_events` "
            "SET `event_name` = %s "
            "WHERE `schema_name`=%s",
            params
        )
        if not cursor.rowcount:
            raise EventDoesNotExist()
