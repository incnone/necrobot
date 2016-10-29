import sqlite3

import mysql.connector

from util import config


## Create new MySQL db (use DATETIME for race_data timestamp and rename character to character_name)
def make_new_database():
    cnx = mysql.connector.connect(user=config.MYSQL_DB_USER, password=config.MYSQL_DB_PASSWD,
                                  host=config.MYSQL_DB_HOST,
                                  database=config.MYSQL_DB_NAME)
    cursor = cnx.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS user_data
                    (discord_id BIGINT,
                    name VARCHAR(200),
                    PRIMARY KEY (discord_id)) ENGINE=InnoDB""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS user_prefs
                    (discord_id BIGINT,
                    hidespoilerchat BOOLEAN,
                    dailyalert INT,
                    racealert INT,
                    PRIMARY KEY (discord_id)) ENGINE=InnoDB""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS daily_data
                    (daily_id INT,
                    type INT,
                    seed INT,
                    msg_id BIGINT,
                    PRIMARY KEY (daily_id, type)) ENGINE=InnoDB""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS daily_races
                    (discord_id BIGINT,
                    daily_id INT,
                    type INT,
                    level TINYINT,
                    time INT,
                    PRIMARY KEY (discord_id, daily_id, type)) ENGINE=InnoDB""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS race_data
                    (race_id INT,
                    timestamp DATETIME,
                    character_name VARCHAR(50),
                    descriptor VARCHAR(100),
                    flags INT,
                    seed INT,
                    PRIMARY KEY (race_id)) ENGINE=InnoDB""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS racer_data
                    (race_id INT,
                    discord_id BIGINT,
                    time BIGINT,
                    rank TINYINT,
                    igt BIGINT,
                    comment VARCHAR(300),
                    level INT,
                    PRIMARY KEY (race_id, discord_id)) ENGINE=InnoDB""")
    cnx.close()



## Transfer user data
def transfer_user_data():
    db = sqlite3.connect(config.DB_FILENAME)
    cnx = mysql.connector.connect(user=config.MYSQL_DB_USER, password=config.MYSQL_DB_PASSWD,
                                  host=config.MYSQL_DB_HOST,
                                  database=config.MYSQL_DB_NAME)
    cursor = cnx.cursor()

    try:
        #user_data
        for row in db.execute('SELECT * FROM user_data'):
            cursor.execute('INSERT INTO user_data (discord_id, name) VALUES (%s,%s)', row)

        #user_prefs
        for row in db.execute('SELECT * FROM user_prefs'):
            cursor.execute('INSERT INTO user_prefs (discord_id, hidespoilerchat, dailyalert, racealert) VALUES (%s,%s,%s,%s)', row)

        cnx.commit()     
    finally:
        db.close()
        cnx.close()          


## Transfer daily data
def transfer_daily_data():
    db = sqlite3.connect(config.DB_FILENAME)
    cnx = mysql.connector.connect(user=config.MYSQL_DB_USER, password=config.MYSQL_DB_PASSWD,
                                  host=config.MYSQL_DB_HOST,
                                  database=config.MYSQL_DB_NAME)
    cursor = cnx.cursor()

    try:

        #daily_data
        for row in db.execute('SELECT * FROM daily_data'):
            cursor.execute('INSERT INTO daily_data (daily_id, type, seed, msg_id) VALUES (%s,%s,%s,%s)', row)

        #daily_races
        for row in db.execute('SELECT * FROM daily_races'):
            cursor.execute('INSERT INTO daily_races (discord_id, daily_id, type, level, time) VALUES (%s,%s,%s,%s,%s)', row)

        cnx.commit()
    finally:
        db.close()
        cnx.close()

## Transfer race data
def transfer_race_data():
    db = sqlite3.connect(config.DB_FILENAME)
    cnx = mysql.connector.connect(user=config.MYSQL_DB_USER, password=config.MYSQL_DB_PASSWD,
                                  host=config.MYSQL_DB_HOST,
                                  database=config.MYSQL_DB_NAME)
    cursor = cnx.cursor()

    try:
        #race_data
        for row in db.execute('SELECT * FROM race_data'):
            cursor.execute('INSERT INTO race_data (race_id, timestamp, character_name, descriptor, flags, seed) VALUES (%s,%s,%s,%s,%s,%s)', row)

        #racer_data
        for row in db.execute('SELECT * FROM racer_data'):
            cursor.execute('INSERT INTO racer_data (race_id, discord_id, time, rank, igt, comment, level) VALUES (%s,%s,%s,%s,%s,%s,%s)', row)
            
        cnx.commit()    
    finally:
        db.close()
        cnx.close()
##-------------------------

config.init('data/bot_config')
make_new_database()
##transfer_user_data()
##transfer_daily_data()
##transfer_race_data()
