import mysql.connector

from .util.config import Config


class NecroDB(object):
    def __init__(self):
        self._number_of_connections = 0

    def _connect(self):
        if self._number_of_connections == 0:
            self._db_conn = mysql.connector.connect(
                user=Config.MYSQL_DB_USER,
                password=Config.MYSQL_DB_PASSWD,
                host=Config.MYSQL_DB_HOST,
                database=Config.MYSQL_DB_NAME)
        self._number_of_connections += 1

    def _close(self):
        self._number_of_connections -= 1
        if self._number_of_connections == 0:
            self._db_conn.close()

    def get_all_users(self, discord_id=None, discord_name=None, twitch_name=None, rtmp_name=None):
        try:
            self._connect()
            cursor = self._db_conn.cursor()

            params = tuple()
            if discord_id is not None:
                params += (int(discord_id),)
            if discord_name is not None:
                params += (discord_name,)
            if twitch_name is not None:
                params += (twitch_name,)
            if rtmp_name is not None:
                params += (rtmp_name,)

            if discord_id is None and discord_name is None and twitch_name is None and rtmp_name is None:
                where_query = 'TRUE'
            else:
                where_query = ''
                if discord_id is not None:
                    where_query += ' AND discord_id=%s'
                if discord_name is not None:
                    where_query += ' AND name=%s'
                if twitch_name is not None:
                    where_query += ' AND twitch_name=%s'
                if rtmp_name is not None:
                    where_query += ' AND rtmp_name=%s'
                where_query = where_query[5:]

            cursor.execute(
                "SELECT discord_id, name, twitch_name, rtmp_name, timezone, user_info, daily_alert, race_alert "
                "FROM user_data "
                "WHERE {0}".format(where_query),
                params)
            return cursor.fetchall()

        finally:
            self._close()

    def get_user_id(self, user_name):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            params = (user_name,)
            cursor.execute(
                "SELECT discord_id "
                "FROM user_data "
                "WHERE name=%s",
                params)
            for row in cursor:
                return row[0]
            return None
        finally:
            self._close()

    def set_prefs(self, params):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            cursor.execute(
                "INSERT INTO user_prefs "
                "(discord_id, hidespoilerchat, dailyalert, racealert) "
                "VALUES (%s,%s,%s,%s) "
                "ON DUPLICATE KEY UPDATE "
                "discord_id=VALUES(discord_id), "
                "hidespoilerchat=VALUES(hidespoilerchat), "
                "dailyalert=VALUES(dailyalert), "
                "racealert=VALUES(racealert)", params)
            self._db_conn.commit()
        finally:
            self._close()

    def get_prefs(self, params):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            cursor.execute("""SELECT * FROM user_prefs WHERE discord_id=%s""", params)
            return cursor.fetchall()
        finally:
            self._close()

    def get_all_matching_prefs(self, pref_type, params):
        if pref_type == "hidespoilerchat":
            query = """SELECT discord_id FROM user_prefs WHERE hidespoilerchat=%s"""
        elif pref_type == "dailyalert":
            query = """SELECT discord_id FROM user_prefs WHERE dailyalert=%s"""
        elif pref_type == "racealert":
            query = """SELECT discord_id FROM user_prefs WHERE racealert=%s"""

        try:
            self._connect()
            cursor = self._db_conn.cursor()
            # noinspection PyUnboundLocalVariable
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            self._close()

    def record_race(self, race):
        try:
            self._connect()
            db_cur = self._db_conn.cursor(buffered=True)
            db_cur.execute(
                "SELECT race_id FROM race_data ORDER BY race_id DESC LIMIT 1")
            new_raceid = 0
            for row in db_cur:
                new_raceid = row[0] + 1
                break

            race_params = (new_raceid,
                           race.start_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                           race.race_info.character_str,
                           race.race_info.descriptor,
                           race.race_info.flags,
                           race.race_info.seed,
                           race.race_info.seeded,
                           race.race_info.amplified,
                           race.race_info.condor_race,
                           race.race_info.private_race,)

            db_cur.execute(
                "INSERT INTO race_data "
                "(race_id, timestamp, character_name, descriptor, flags, seed, seeded, amplified, condor, private) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                race_params)

            racer_list = []
            max_time = 0
            for racer in race.racers:
                racer_list.append(racer)
                if racer.is_finished:
                    max_time = max(racer.time, max_time)
            max_time += 1

            racer_list.sort(key=lambda r: r.time if r.is_finished else max_time)

            rank = 1
            for racer in racer_list:
                racer_params = (new_raceid, racer.id, racer.time, rank, racer.igt, racer.comment, racer.level)
                db_cur.execute(
                    "INSERT INTO racer_data "
                    "(race_id, discord_id, time, rank, igt, comment, level) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    racer_params)
                if racer.is_finished:
                    rank += 1

                user_params = (racer.id, racer.name)
                db_cur.execute(
                    'INSERT INTO user_data '
                    '(discord_id, name) '
                    'VALUES (%s,%s) '
                    'ON DUPLICATE KEY UPDATE '
                    'discord_id=VALUES(discord_id), '
                    'name=VALUES(name)',
                    user_params)

            self._db_conn.commit()
        finally:
            self._close()

    def register_all_users(self, members):
        try:
            self._connect()
            db_cur = self._db_conn.cursor()
            for member in members:
                params = (member.id, member.name,)
                db_cur.execute(
                    "INSERT IGNORE INTO user_data (discord_id, name) VALUES (%s,%s)",
                    params)
            self._db_conn.commit()
        finally:
            self._close()

    def register_user(self, member):
        try:
            self._connect()
            params = (member.id, member.name,)
            cursor = self._db_conn.cursor()
            cursor.execute(
                "INSERT INTO user_data (discord_id, name) VALUES (%s,%s)",
                params)
            self._db_conn.commit()
        finally:
            self._close()

    def get_daily_seed(self, params):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            cursor.execute(
                "SELECT seed FROM daily_data WHERE daily_id=%s AND type=%s",
                params)
            return cursor.fetchall()
        finally:
            self._close()

    def get_daily_times(self, params):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            cursor.execute(
                "SELECT user_data.name,daily_races.level,daily_races.time "
                "FROM daily_races INNER JOIN user_data ON daily_races.discord_id=user_data.discord_id "
                "WHERE daily_races.daily_id=%s AND daily_races.type=%s "
                "ORDER BY daily_races.level DESC, daily_races.time ASC",
                params)
            return cursor.fetchall()
        finally:
            self._close()

    def has_submitted_daily(self, params):
        try:
            self._connect()
            cursor = self._db_conn.cursor(buffered=True)
            cursor.execute(
                "SELECT level FROM daily_races WHERE discord_id=%s AND daily_id=%s AND type=%s",
                params)
            for row in cursor:
                if row[0] != -1:
                    return True
            return False
        finally:
            self._close()

    def has_registered_daily(self, params):
        try:
            self._connect()
            cursor = self._db_conn.cursor(buffered=True)
            cursor.execute(
                "SELECT * FROM daily_races WHERE discord_id=%s AND daily_id=%s AND type=%s",
                params)
            for _ in cursor:
                return True
            return False
        finally:
            self._close()

    def register_daily(self, params):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            cursor.execute(
                "INSERT INTO daily_races "
                "(discord_id, daily_id, type, level, time) "
                "VALUES (%s,%s,%s,%s,%s) "
                "ON DUPLICATE KEY UPDATE "
                "discord_id=VALUES(discord_id), "
                "daily_id=VALUES(daily_id), "
                "type=VALUES(type), "
                "level=VALUES(level), "
                "time=VALUES(time)",
                params)
            self._db_conn.commit()
        finally:
            self._close()

    def registered_daily(self, params):
        try:
            self._connect()
            cursor = self._db_conn.cursor(buffered=True)
            cursor.execute(
                "SELECT daily_id FROM daily_races WHERE discord_id=%s AND type=%s ORDER BY daily_id DESC",
                params)
            return cursor.fetchall()
        finally:
            self._close()

    def submitted_daily(self, params):
        try:
            self._connect()
            cursor = self._db_conn.cursor(buffered=True)
            cursor.execute(
                "SELECT daily_id,level FROM daily_races WHERE discord_id=%s AND type=%s ORDER BY daily_id DESC",
                params)
            return cursor.fetchall()
        finally:
            self._close()

    def delete_from_daily(self, params):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            cursor.execute(
                "UPDATE daily_races SET level=%s WHERE discord_id=%s AND daily_id=%s AND type=%s",
                params)
            self._db_conn.commit()
        finally:
            self._close()

    def create_daily(self, params):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            cursor.execute(
                "INSERT INTO daily_data (daily_id, type, seed, msg_id) VALUES (%s,%s,%s,%s)",
                params)
            self._db_conn.commit()
        finally:
            self._close()

    def update_daily(self, params):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            cursor.execute(
                "UPDATE daily_data SET msg_id=%s WHERE daily_id=%s AND type=%s",
                params)
            self._db_conn.commit()
        finally:
            self._close()

    def get_daily_message_id(self, params):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            cursor.execute(
                "SELECT msg_id FROM daily_data WHERE daily_id=%s AND type=%s",
                params)
            return cursor.fetchall()
        finally:
            self._close()

    def get_allzones_race_numbers(self, discord_id, amplified):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            params = (discord_id,)
            cursor.execute(
                "SELECT race_data.character_name, COUNT(*) as num "
                "FROM racer_data "
                "JOIN race_data ON race_data.race_id = racer_data.race_id "
                "WHERE racer_data.discord_id = %s "
                "AND race_data.descriptor = 'All-zones' " +
                ("AND race_data.amplified " if amplified else "AND NOT race_data.amplified ") +
                "AND race_data.seeded AND NOT race_data.private "
                "GROUP BY race_data.character_name, race_data.descriptor, race_data.flags "
                "ORDER BY num DESC",
                params)
            return cursor.fetchall()
        finally:
            self._close()

    def get_all_racedata(self, discord_id, char_name, amplified):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            params = (discord_id, char_name)
            cursor.execute(
                "SELECT racer_data.time, racer_data.level "
                "FROM racer_data "
                "JOIN race_data ON race_data.race_id = racer_data.race_id "
                "WHERE racer_data.discord_id = %s "
                "AND race_data.character_name = %s "
                "AND race_data.descriptor = 'All-zones' " +
                ("AND race_data.amplified " if amplified else "AND NOT race_data.amplified ") +
                "AND race_data.seeded AND NOT race_data.private ",
                params)
            return cursor.fetchall()
        finally:
            self._close()

    def get_fastest_times_leaderboard(self, character_name, amplified, limit):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            params = (character_name, limit,)
            cursor.execute(
                "SELECT user_data.name, racer_data.time, race_data.seed, race_data.timestamp "
                "FROM racer_data "
                "INNER JOIN "
                "( "
                "    SELECT discord_id, MIN(time) AS min_time "
                "    FROM racer_data INNER JOIN race_data ON race_data.race_id = racer_data.race_id "
                "    WHERE "
                "        time > 0 "
                "        AND level = -2 "
                "        AND race_data.character_name=%s "
                "        AND race_data.descriptor='All-zones' "
                "        AND race_data.seeded " +
                "        AND {0}race_data.amplified ".format('' if amplified else 'NOT ') +
                "        AND NOT race_data.private "
                "    Group By discord_id "
                ") rd1 On rd1.discord_id = racer_data.discord_id "
                "INNER JOIN user_data ON user_data.discord_id = racer_data.discord_id "
                "INNER JOIN race_data ON race_data.race_id = racer_data.race_id "
                "WHERE racer_data.time = rd1.min_time "
                "ORDER BY racer_data.time ASC "
                "LIMIT %s",
                params)
            return cursor.fetchall()
        finally:
            self._close()

    def get_most_races_leaderboard(self, character_name, limit):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            params = (character_name, character_name, limit,)
            cursor.execute(
                "SELECT "
                "    user_name, "
                "    num_predlc + num_postdlc as total, "
                "    num_predlc, "
                "    num_postdlc "
                "FROM "
                "( "
                "    SELECT "
                "        user_data.name as user_name, "
                "        SUM( "
                "                IF( "
                "                race_data.character_name=%s "
                "                AND race_data.descriptor='All-zones' "
                "                AND NOT race_data.amplified "
                "                AND NOT race_data.private, "
                "                1, 0 "
                "                ) "
                "        ) as num_predlc, "
                "        SUM( "
                "                IF( "
                "                race_data.character_name=%s "
                "                AND race_data.descriptor='All-zones' "
                "                AND race_data.amplified "
                "                AND NOT race_data.private, "
                "                1, 0 "
                "                ) "
                "        ) as num_postdlc "
                "    FROM racer_data "
                "    JOIN user_data ON user_data.discord_id = racer_data.discord_id "
                "    JOIN race_data ON race_data.race_id = racer_data.race_id "
                "    GROUP BY user_data.name "
                ") tbl1 "
                "ORDER BY total DESC "
                "LIMIT %s",
                params)
            return cursor.fetchall()
        finally:
            self._close()

    def get_largest_race_number(self, discord_id):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            params = (discord_id,)
            cursor.execute(
                "SELECT race_id "
                "FROM racer_data "
                "WHERE discord_id = %s "
                "ORDER BY race_id DESC "
                "LIMIT 1",
                params)
            for row in cursor:
                return int(row[0])
            return 0
        finally:
            self._close()

    def set_timezone(self, discord_id, timezone):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            params = (timezone, discord_id,)
            cursor.execute(
                "UPDATE user_data "
                "SET timezone=%s "
                "WHERE discord_id=%s",
                params)
            self._db_conn.commit()
        finally:
            self._close()

    def set_rtmp(self, discord_id, rtmp_name):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            params = (rtmp_name, discord_id,)
            cursor.execute(
                "UPDATE user_data "
                "SET rtmp_name=%s "
                "WHERE discord_id=%s",
                params)
            self._db_conn.commit()
        finally:
            self._close()

    def set_twitch(self, discord_id, twitch_name):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            params = (twitch_name, discord_id,)
            cursor.execute(
                "UPDATE user_data "
                "SET twitch_name=%s "
                "WHERE discord_id=%s",
                params)
            self._db_conn.commit()
        finally:
            self._close()

    def set_user_info(self, discord_id, user_info):
        try:
            self._connect()
            cursor = self._db_conn.cursor()
            params = (user_info, discord_id,)
            cursor.execute(
                "UPDATE user_data "
                "SET user_info=%s "
                "WHERE discord_id=%s",
                params)
            self._db_conn.commit()
        finally:
            self._close()
