"""
Interaction with the races, race_types, and race_runs databases (necrobot or condor event schema).
"""

from necrobot.database.dbconnect import DBConnect
from necrobot.database.dbutil import tn
from necrobot.race.race import Race
from necrobot.race.raceinfo import RaceInfo


# Record a race-------------------------------------------------------------------
async def record_race(race: Race) -> None:
    type_id = await get_race_type_id(race.race_info, register=True)

    async with DBConnect(commit=True) as cursor:
        # Record the race
        race_params = (
            race.start_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            type_id,
            race.race_info.seed,
            race.race_info.condor_race,
            race.race_info.private_race,
        )

        cursor.execute(
            """
            INSERT INTO {0} 
                (timestamp, type_id, seed, condor, private) 
            VALUES (%s,%s,%s,%s,%s)
            """.format(tn('races')),
            race_params
        )

        # Store the new race ID in the Race object
        cursor.execute("SELECT LAST_INSERT_ID()")
        race.race_id = int(cursor.fetchone()[0])

        # Record each racer in race_runs
        rank = 1
        for racer in race.racers:
            racer_params = (race.race_id, racer.user_id, racer.time, rank, racer.igt, racer.comment, racer.level)
            cursor.execute(
                """
                INSERT INTO {0} 
                    (race_id, user_id, time, rank, igt, comment, level) 
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """.format(tn('race_runs')),
                racer_params
            )
            if racer.is_finished:
                rank += 1


# Race type functions-------------------------------------------------------------------
async def get_race_type_id(race_info: RaceInfo, register: bool = False) -> int or None:
    params = (
        race_info.character_str,
        race_info.descriptor,
        race_info.seeded,
        race_info.amplified,
        race_info.seed_fixed,
    )

    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT `type_id` 
            FROM `race_types` 
            WHERE `character`=%s 
               AND `descriptor`=%s 
               AND `seeded`=%s 
               AND `amplified`=%s 
               AND `seed_fixed`=%s 
            LIMIT 1
            """,
            params
        )

        row = cursor.fetchone()
        if row is not None:
            return int(row[0])

    # If here, the race type was not found
    if not register:
        return None

    # Create the new race type
    async with DBConnect(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO race_types 
            (`character`, descriptor, seeded, amplified, seed_fixed) 
            VALUES (%s, %s, %s, %s, %s)
            """,
            params
        )
        cursor.execute("SELECT LAST_INSERT_ID()")
        return int(cursor.fetchone()[0])


async def get_race_info_from_type_id(race_type: int) -> RaceInfo or None:
    params = (race_type,)
    async with DBConnect(commit=False) as cursor:
        cursor.execute(
            """
            SELECT `character`, `descriptor`, `seeded`, `amplified`, `seed_fixed` 
            FROM `race_types` 
            WHERE `type_id`=%s
            """,
            params
        )

        row = cursor.fetchone()
        if row is not None:
            race_info = RaceInfo()
            race_info.set_char(row[0])
            race_info.descriptor = row[1]
            race_info.seeded = bool(row[2])
            race_info.amplified = bool(row[3])
            race_info.seed_fixed = bool(row[4])
            return race_info
        else:
            return None


# Stat functions-------------------------------------------------------------------
async def get_allzones_race_numbers(user_id: int, amplified: bool) -> list:
    async with DBConnect(commit=False) as cursor:
        params = (user_id,)
        cursor.execute(
            """
            SELECT `race_types`.`character`, COUNT(*) as num 
            FROM {1} 
                INNER JOIN {0} ON {0}.`race_id` = {1}.`race_id` 
                INNER JOIN race_types ON {0}.`type_id` = `race_types`.`type_id` 
            WHERE {1}.`user_id` = %s 
                AND `race_types`.`descriptor` = 'All-zones' 
                AND {2}`race_types`.`amplified` 
                AND `race_types`.`seeded` AND NOT {0}.`private` 
            GROUP BY `race_types`.`character` 
            ORDER BY num DESC
            """.format(tn('races'), tn('race_runs'), 'NOT ' if not amplified else ''),
            params)
        return cursor.fetchall()


async def get_all_racedata(user_id: int, char_name: str, amplified: bool) -> list:
    async with DBConnect(commit=False) as cursor:
        params = (user_id, char_name)
        cursor.execute(
            """
            SELECT {1}.`time`, {1}.`level` 
            FROM {1} 
                INNER JOIN {0} ON {0}.`race_id` = {1}.`race_id` 
                INNER JOIN `race_types` ON {0}.`type_id` = `race_types`.`type_id` 
            WHERE {1}.`user_id` = %s 
                AND `race_types`.`character` = %s 
                AND `race_types`.`descriptor` = 'All-zones' 
                AND {2}`race_types`.`amplified` 
                AND race_types.seeded AND NOT {0}.`private`
            """.format(tn('races'), tn('race_runs'), 'NOT ' if not amplified else ''),
            params
        )
        return cursor.fetchall()


async def get_fastest_times_leaderboard(character_name: str, amplified: bool, limit: int) -> list:
    async with DBConnect(commit=False) as cursor:
        params = (character_name, limit,)
        cursor.execute(
            """
            SELECT users.discord_name, {race_runs}.time, {races}.seed, {races}.timestamp 
            FROM {race_runs} 
                INNER JOIN 
                ( 
                    SELECT user_id, MIN(time) AS min_time 
                    FROM {race_runs} 
                        INNER JOIN {races} ON {races}.race_id = {race_runs}.race_id 
                        INNER JOIN race_types ON race_types.type_id = {races}.type_id 
                    WHERE 
                        {race_runs}.time > 0 
                        AND {race_runs}.level = -2 
                        AND ({races}.timestamp > '2017-07-12' OR NOT race_types.amplified)
                        AND race_types.character=%s 
                        AND race_types.descriptor='All-zones' 
                        AND race_types.seeded 
                        AND {not_amplified}race_types.amplified 
                        AND NOT {races}.private 
                    GROUP BY user_id 
                ) rd1 On rd1.user_id = {race_runs}.user_id 
                INNER JOIN users ON users.user_id = {race_runs}.user_id 
                INNER JOIN {races} ON {races}.race_id = {race_runs}.race_id 
            WHERE {race_runs}.time = rd1.min_time 
            ORDER BY {race_runs}.time ASC 
            LIMIT %s
            """.format(races=tn('races'), race_runs=tn('race_runs'), not_amplified=('' if amplified else 'NOT ')),
            params)
        return cursor.fetchall()


async def get_most_races_leaderboard(character_name: str, limit: int) -> list:
    async with DBConnect(commit=False) as cursor:
        params = (character_name, character_name, limit,)
        cursor.execute(
            """
            SELECT 
                user_name, 
                num_predlc + num_postdlc as total, 
                num_predlc, 
                num_postdlc 
            FROM 
            ( 
                SELECT 
                    users.discord_name as user_name, 
                    SUM( 
                            IF( 
                               race_types.character=%s 
                               AND race_types.descriptor='All-zones' 
                               AND NOT race_types.amplified 
                               AND NOT {0}.private, 
                               1, 0 
                            ) 
                    ) as num_predlc, 
                    SUM( 
                            IF( 
                               race_types.character=%s 
                               AND race_types.descriptor='All-zones' 
                               AND race_types.amplified 
                               AND NOT {0}.private, 
                               1, 0 
                            ) 
                    ) as num_postdlc 
                FROM {1} 
                    INNER JOIN users ON users.user_id = {1}.user_id 
                    INNER JOIN {0} ON {0}.race_id = {1}.race_id 
                    INNER JOIN race_types ON race_types.type_id = {0}.type_id 
                GROUP BY users.discord_name 
            ) tbl1 
            ORDER BY total DESC 
            LIMIT %s
            """.format(tn('races'), tn('race_runs')),
            params)
        return cursor.fetchall()


async def get_largest_race_number(user_id: int) -> int:
    async with DBConnect(commit=False) as cursor:
        params = (user_id,)
        cursor.execute(
            """
            SELECT race_id 
            FROM {0} 
            WHERE user_id = %s 
            ORDER BY race_id DESC 
            LIMIT 1
            """.format(tn('race_runs')),
            params)
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0
