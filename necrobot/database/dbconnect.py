import asyncio
import mysql.connector

from necrobot.util import console
from necrobot.config import Config


class DBConnect(object):
    _lock = asyncio.Lock()
    _db_connection = None

    def __init__(self, commit=False):
        self.cursor = None
        self.commit = commit

    async def __aenter__(self):
        await DBConnect._lock.acquire()
        try:
            return self.__enter__()
        except Exception:
            DBConnect._lock.release()
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            return self.__exit__(exc_type, exc_val, exc_tb)
        finally:
            DBConnect._lock.release()

    def __enter__(self):
        if DBConnect._db_connection is None:
            DBConnect._db_connection = mysql.connector.connect(
                user=Config.MYSQL_DB_USER,
                password=Config.MYSQL_DB_PASSWD,
                host=Config.MYSQL_DB_HOST,
                database=Config.MYSQL_DB_NAME)
        elif not DBConnect._db_connection.is_connected():
            DBConnect._db_connection.reconnect()

        if not DBConnect._db_connection.is_connected():
            raise RuntimeError('Couldn\'t connect to the MySQL database.')

        if Config.debugging():
            self.cursor = LoggingCursor(DBConnect._db_connection.cursor())
        else:
            self.cursor = DBConnect._db_connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        if exc_type is None and self.commit:
            DBConnect._db_connection.commit()
        elif self.commit:
            DBConnect._db_connection.rollback()


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
        console.debug('Execute SQL: <{0}> <args={1}> <kwargs={2}>'.format(operation, args, kwargs))
        return self.cursor.execute(operation, *args, **kwargs)
