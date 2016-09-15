import config
import mysql.connector

class NecroDB():

    def _connect(self):
        self._db_conn = mysql.connector.connect(user=config.MYSQL_DB_USER, password=config.MYSQL_DB_PASSWD, host=config.MYSQL_DB_HOST, database=config.MYSQL_DB_NAME)

    def _close(self):
        self._db_conn.close()

    def set_prefs(self, params):
        self._connect()
        cursor = self._db_conn.cursor()
        cursor.execute("""INSERT INTO user_prefs (discord_id, hidespoilerchat, dailyalert, racealert) VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE discord_id=VALUES(discord_id), hidespoilerchat=VALUES(hidespoilerchat), dailyalert=VALUES(dailyalert), racealert=VALUES(racealert)""", params)         
        self._db_conn.commit()
        self._close()

    def get_prefs(self, params):
        self._connect()     
        cursor = self._db_conn.cursor()
        cursor.execute("""SELECT * FROM user_prefs WHERE discord_id=%s""", params)
        prefs = cursor.fetchall()
        self._close()
        return prefs

    def get_all_matching_prefs(self, type, params):
        if type == "hidespoilerchat":
            query = """SELECT discord_id FROM user_prefs WHERE hidespoilerchat=%s"""
        elif type == "dailyalert":
            query = """SELECT discord_id FROM user_prefs WHERE dailyalert=%s OR dailyalert=%s"""
        elif type == "racealert":
            query = """SELECT discord_id FROM user_prefs WHERE racealert=%s OR racealert=%s"""
        self._connect()
        cursor = self._db_conn.cursor()
        cursor.execute(query, params)
        prefs = cursor.fetchall()
        self._close()
        return prefs
