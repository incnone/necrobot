import mysql.connector
from necrobot.util.config import Config


# Create new MySQL db (use DATETIME for race_data timestamp and rename character to character_name)
def make_new_database():
    cnx = mysql.connector.connect(user=Config.MYSQL_DB_USER, password=Config.MYSQL_DB_PASSWD,
                                  host=Config.MYSQL_DB_HOST,
                                  database=Config.MYSQL_DB_NAME)
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

# ------------------------

if __name__ == "__main__":
    pass
    # config.init('data/bot_config')
    # make_new_database()
