"""
Interaction with the necrobot.condor_events table.
"""

import re
from necrobot.config import Config
from necrobot.database.dbconnect import DBConnect


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
