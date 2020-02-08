import re
from typing import Optional

import necrobot.exception
from necrobot.condorbot.condorevent import CondorEvent
from necrobot.config import Config
from necrobot.database.dbconnect import DBConnect


async def is_condor_event(schema_name: str) -> bool:
    """
    Parameters
    ----------
    schema_name: str
        The name of the schema for the event (and also the event's unique identifier).

    Returns
    -------
    bool:
        Whether the given schema refers to a CoNDOR event.
    """
    params = (schema_name,)
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT `schema_name` 
            FROM `events`
            WHERE `schema_name` = %s
            LIMIT 1
            """,
            params
        )
        for _ in cursor:
            return True

        return False


async def set_event_params(
    schema_name: str,
    event_name: Optional[str] = None,
    deadline: Optional[str] = None,
    gsheet_id: Optional[str] = None
):
    """
    Parameters
    ----------
    schema_name: str
        The name of the schema to set.
    event_name: str
        The name to set the event to, if not None (otherwise, does nothing)
    deadline: str
        The string representing the deadline, if not None (otherwise, does nothing)
    gsheet_id: str
        The ID of the GSheet, if not None (otherwise, does nothing)
    """
    async with DBConnect(commit=True) as cursor:
        if event_name is not None:
            params = (event_name, schema_name,)
            cursor.execute(
                """
                UPDATE `events`
                SET `event_name` = %s
                WHERE `schema_name` = %s
                """,
                params
            )
        if deadline is not None:
            params = (deadline, schema_name,)
            cursor.execute(
                """
                UPDATE `events`
                SET `deadline` = %s
                WHERE `schema_name` = %s
                """,
                params
            )
        if gsheet_id is not None:
            params = (gsheet_id, schema_name,)
            cursor.execute(
                """
                UPDATE `events`
                SET `gsheet_id` = %s
                WHERE `schema_name` = %s
                """,
                params
            )


async def get_event(schema_name: str) -> CondorEvent:
    """
    Parameters
    ----------
    schema_name: str
        The name of the schema for the event (and also the event's unique identifier).

    Returns
    -------
    str:
        The string representing the deadline
    """
    params = (schema_name,)
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT `event_name`, `deadline`, `gsheet_id`
            FROM `events`
            WHERE `schema_name` = %s
            LIMIT 1
            """,
            params
        )
        for row in cursor:
            return CondorEvent(schema_name=schema_name, event_name=row[0], deadline_str=row[1], gsheet_id=row[2])

    raise necrobot.exception.SchemaDoesNotExist()


async def create_event(schema_name: str) -> CondorEvent:
    """Creates a new CoNDOR event with the given schema_name as its database.

    Parameters
    ----------
    schema_name: str
        The name of the database schema for this event, and also the unique identifier for this event.

    Raises
    ------
    SchemaAlreadyExists
        When the schema_name already exists.
    """
    table_name_validator = re.compile(r'^[0-9a-zA-Z_$]+$')
    if not table_name_validator.match(schema_name):
        raise necrobot.exception.InvalidSchemaName()

    params = (schema_name,)
    async with DBConnect(commit=True) as cursor:
        cursor.execute(
            """
            SELECT `schema_name`
            FROM `events` 
            WHERE `schema_name`=%s
            """,
            params
        )
        for _ in cursor:
            raise necrobot.exception.SchemaAlreadyExists('Event already exists.')

        cursor.execute(
            """
            SELECT SCHEMA_NAME 
            FROM INFORMATION_SCHEMA.SCHEMATA 
            WHERE SCHEMA_NAME = %s
            """,
            params
        )
        for _ in cursor:
            raise necrobot.exception.SchemaAlreadyExists('Schema already exists, but is not a CoNDOR event.')

        cursor.execute(
            """
            CREATE SCHEMA `{schema_name}` 
            DEFAULT CHARACTER SET = utf8 
            DEFAULT COLLATE = utf8_general_ci
            """.format(schema_name=schema_name)
        )
        cursor.execute(
            """
            INSERT INTO `events` 
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

        for table_name in ['leagues', 'matches', 'match_races', 'races', 'race_runs']:
            cursor.execute(
                "CREATE TABLE `{league_schema}`.`{table}` LIKE `{necrobot_schema}`.`{table}`".format(
                    league_schema=schema_name,
                    necrobot_schema=Config.MYSQL_DB_NAME,
                    table=table_name
                )
            )

        def tablename(table):
            return '`{league_schema}`.`{table}`'.format(league_schema=schema_name, table=table)

        cursor.execute(
            """
            CREATE VIEW {race_summary} AS
                SELECT 
                    {matches}.`match_id` AS `match_id`,
                    {matches}.`league_tag` AS `league_tag`,
                    {match_races}.`race_number` AS `race_number`,
                    `users_winner`.`user_id` AS `winner_id`,
                    `users_loser`.`user_id` AS `loser_id`,
                    `race_runs_winner`.`time` AS `winner_time`,
                    `race_runs_loser`.`time` AS `loser_time`
                FROM
                    {matches}
                    JOIN {match_races} ON {matches}.`match_id` = {match_races}.`match_id`
                    JOIN `users` `users_winner` ON 
                        IF( {match_races}.`winner` = 1, 
                            `users_winner`.`user_id` = {matches}.`racer_1_id`, 
                            `users_winner`.`user_id` = {matches}.`racer_2_id`
                        )
                    JOIN `users` `users_loser` ON 
                        IF( {match_races}.`winner` = 1, 
                            `users_loser`.`user_id` = {matches}.`racer_2_id`, 
                            `users_loser`.`user_id` = {matches}.`racer_1_id`
                        )
                    LEFT JOIN {race_runs} `race_runs_winner` ON 
                        `race_runs_winner`.`user_id` = `users_winner`.`user_id`
                        AND `race_runs_winner`.`race_id` = {match_races}.`race_id`
                    LEFT JOIN {race_runs} `race_runs_loser` ON 
                        `race_runs_loser`.`user_id` = `users_loser`.`user_id`
                        AND `race_runs_loser`.`race_id` = {match_races}.`race_id`
                WHERE NOT {match_races}.`canceled`
            """.format(
                matches=tablename('matches'),
                match_races=tablename('match_races'),
                race_runs=tablename('race_runs'),
                race_summary=tablename('race_summary')
            )
        )

        cursor.execute(
            """
            CREATE VIEW {match_info} AS
                SELECT 
                    {matches}.`match_id` AS `match_id`,
                    {matches}.`league_tag` AS `league_tag`,
                    `ud1`.`twitch_name` AS `racer_1_name`,
                    `ud2`.`twitch_name` AS `racer_2_name`,
                    {matches}.`suggested_time` AS `scheduled_time`,
                    `ud3`.`twitch_name` AS `cawmentator_name`,
                    {matches}.`vod` AS `vod`,
                    {matches}.`is_best_of` AS `is_best_of`,
                    {matches}.`number_of_races` AS `number_of_races`,
                    {matches}.`autogenned` AS `autogenned`,
                    ({matches}.`r1_confirmed` AND {matches}.`r2_confirmed`) AS `scheduled`,
                    COUNT(0) AS `num_finished`,
                    SUM((CASE
                        WHEN ({match_races}.`winner` = 1) THEN 1
                        ELSE 0
                    END)) AS `racer_1_wins`,
                    SUM((CASE
                        WHEN ({match_races}.`winner` = 2) THEN 1
                        ELSE 0
                    END)) AS `racer_2_wins`,
                    (CASE
                        WHEN
                            {matches}.`is_best_of`
                        THEN
                            (GREATEST(SUM((CASE
                                        WHEN ({match_races}.`winner` = 1) THEN 1
                                        ELSE 0
                                    END)),
                                    SUM((CASE
                                        WHEN ({match_races}.`winner` = 2) THEN 1
                                        ELSE 0
                                    END))) >= (({matches}.`number_of_races` DIV 2) + 1))
                        ELSE (COUNT(0) >= {matches}.`number_of_races`)
                    END) AS `completed`
                FROM
                    (((({matches}
                    LEFT JOIN {match_races} ON (({matches}.`match_id` = {match_races}.`match_id`)))
                    JOIN `necrobot`.`users` `ud1` ON (({matches}.`racer_1_id` = `ud1`.`user_id`)))
                    JOIN `necrobot`.`users` `ud2` ON (({matches}.`racer_2_id` = `ud2`.`user_id`)))
                    LEFT JOIN `necrobot`.`users` `ud3` ON (({matches}.`cawmentator_id` = `ud3`.`user_id`)))
                WHERE
                    ({match_races}.`canceled` = 0 OR {match_races}.`canceled` IS NULL)
                GROUP BY {matches}.`match_id`
            """.format(
                match_info=tablename('match_info'),
                matches=tablename('matches'),
                match_races=tablename('match_races')
            )
        )

        cursor.execute(
            """
            CREATE VIEW {event_info} AS
                SELECT *
                FROM `events`
                WHERE (`events`.`schema_name` = %s)
            """.format(event_info=tablename('event_info')),
            params
        )

    return CondorEvent(schema_name=schema_name, event_name=None, deadline_str=None, gsheet_id=None)
