import mysql.connector

from necrobot.util import console
from necrobot.config import Config


class DBConnect(object):
    db_connection = None

    def __init__(self, commit=False):
        self.cursor = None
        self.commit = commit

    def __enter__(self):
        if DBConnect.db_connection is None:
            DBConnect.db_connection = mysql.connector.connect(
                user=Config.MYSQL_DB_USER,
                password=Config.MYSQL_DB_PASSWD,
                host=Config.MYSQL_DB_HOST,
                database=Config.MYSQL_DB_NAME)
        elif not DBConnect.db_connection.is_connected():
            DBConnect.db_connection.reconnect()

        if not DBConnect.db_connection.is_connected():
            raise RuntimeError('Couldn\'t connect to the MySQL database.')

        if Config.debugging():
            self.cursor = LoggingCursor(DBConnect.db_connection.cursor())
        else:
            self.cursor = DBConnect.db_connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        if exc_type is None and self.commit:
            DBConnect.db_connection.commit()
        elif self.commit:
            DBConnect.db_connection.rollback()


class LoggingCursor(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def __getattr__(self, name):
        return getattr(self.cursor, name)

    def __next__(self):
        return self.cursor.__next__()

    def __iter__(self):
        return self.cursor.__iter__()

    def execute(self, operation, *args, **kwargs):
        console.debug(operation)
        return self.cursor.execute(operation, *args, **kwargs)
