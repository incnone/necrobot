"""
Interaction with the necrobot.condor_events table.
"""

from necrobot.database.dbconnect import DBConnect


class EventAlreadyExists(Exception):
    def __init__(self, exc_str):
        self._exc_str = exc_str

    def __str__(self):
        return self._exc_str if self._exc_str is not None else ''


class EventDoesNotExist(Exception):
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
            "CREATE SCHEMA %s "
            "DEFAULT CHARACTER SET = utf8 "
            "DEFAULT COLLATE = utf8_general_ci",
            params
        )
        cursor.execute(
            "INSERT INTO condor_events "
            "(`schema_name`) "
            "VALUES (%s)",
            params
        )


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
    with DBConnect(commit=True) as cursor:
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

