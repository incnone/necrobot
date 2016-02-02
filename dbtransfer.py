import codecs
#import config
import sqlite3

DATABASE_NAMES = ['data/daily.db', 'data/races.db', 'data/users.db']
#DB_OUT_NAME = config.DB_FILENAME
DB_OUT_NAME = 'data/necrobot.db'

### Step 1: Dump each table from the databases into a .dmp file. The files will be one line per row,
### each line a comma-separated list enclosed in parentheses (a,b,c,d,e). Text is enclosed in single quotes
### or double quotes when contains an apostrophe.
##def dump_old_databases():
##    for db_name in DATABASE_NAMES:
##        db_conn = sqlite3.connect(db_name)
##
##        for row in db_conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
##            table_name = row[0]
##            print(table_name)
##            f = codecs.open('{}.dmp'.format(table_name), 'w', 'utf-8')
##            for t_row in  db_conn.execute('SELECT * from ' + table_name):                
##                try:
##                    print(t_row, file=f)
##                except UnicodeEncodeError:
##                    print('Unicode error.')
##                    continue
##                
##            f.close()
##        db_conn.close()

## Make the new master database, with tables set up as we want them
def make_new_database():
    db_conn = sqlite3.connect(DB_OUT_NAME)
    db_conn.execute("""CREATE TABLE user_data
                    (discord_id bigint,
                    name text,
                    PRIMARY KEY (discord_id) ON CONFLICT REPLACE)""")
    db_conn.execute("""CREATE TABLE user_prefs
                    (discord_id bigint REFERENCES user_data (discord_id),
                    hidespoilerchat boolean,
                    dailyalert int,
                    racealert int,
                    PRIMARY KEY (discord_id) ON CONFLICT REPLACE)""")
    db_conn.execute("""CREATE TABLE daily_data
                    (daily_id int,
                    type int,
                    seed int,
                    msg_id bigint,
                    PRIMARY KEY (daily_id, type) ON CONFLICT ABORT)""")
    db_conn.execute("""CREATE TABLE daily_races
                    (discord_id bigint REFERENCES user_data (discord_id),
                    daily_id int REFERENCES daily_data (daily_id),
                    type int REFERENCES daily_data (type),
                    level tinyint,
                    time int,
                    PRIMARY KEY (discord_id, daily_id, type) ON CONFLICT REPLACE)""")
    db_conn.execute("""CREATE TABLE race_data
                    (race_id integer,
                    timestamp bigint,
                    character text,
                    descriptor text,
                    flags int,
                    seed int,
                    PRIMARY KEY (race_id) ON CONFLICT ABORT)""")
    db_conn.execute("""CREATE TABLE racer_data
                    (race_id int REFERENCES race_data (race_id),
                    discord_id bigint REFERENCES user_data (discord_id),
                    time bigint,
                    rank tinyint,
                    igt bigint,
                    comment text,
                    level int,
                    PRIMARY KEY (race_id, discord_id) ON CONFLICT ABORT)""")
    db_conn.commit()
    db_conn.close()

## Transfer data from daily.db
def transfer_daily_data():
    db_old = sqlite3.connect('data/daily.db')
    db_old.row_factory = sqlite3.Row
    db_new = sqlite3.connect(DB_OUT_NAME)

    try:
        #daily_seeds
        for row in db_old.execute('SELECT * FROM daily_seeds'):
            params = (row['date'], 0, row['seed'], row['msgid'],)
            db_new.execute('INSERT INTO daily_data (daily_id, type, seed, msg_id) VALUES (?,?,?,?)', params)

        #last_daily
        for row in db_old.execute('SELECT * FROM last_daily'):
            ld_params = (row['playerid'], row['date'], 0, -1, -1,)
            db_new.execute('INSERT INTO daily_races (discord_id, daily_id, type, level, time) VALUES (?,?,?,?,?)', ld_params)

        #daily_races
        for row in db_old.execute('SELECT * FROM daily_races'):
            ud_params = (row['playerid'], row['name'],)
            db_new.execute('INSERT INTO user_data (discord_id, name) VALUES (?,?)', ud_params)
            dr_params = (row['playerid'], row['date'], 0, row['level'], row['time'],)
            db_new.execute('INSERT INTO daily_races (discord_id, daily_id, type, level, time) VALUES (?,?,?,?,?)', dr_params)

        db_new.commit()
    finally:
        db_old.close()
        db_new.close()

## Transfer data from race.db
def transfer_race_data():
    db_old = sqlite3.connect('data/races.db')
    db_old.row_factory = sqlite3.Row
    db_new = sqlite3.connect(DB_OUT_NAME)

    try:
        #race_data
        for row in db_old.execute('SELECT * FROM race_data'):
            race_flag = 1 if row['seeded'] else 0
            params = (row['raceid'], row['timestamp'], row['character'], row['descriptor'], race_flag, row['seed'])
            db_new.execute('INSERT INTO race_data (race_id, timestamp, character, descriptor, flags, seed) VALUES (?,?,?,?,?,?)', params)

        #racer_data
        for row in db_old.execute('SELECT * FROM racer_data'):
            ud_params = (row['playerid'], row['name'],)
            db_new.execute('INSERT INTO user_data (discord_id, name) VALUES (?,?)', ud_params)
            level = 18 if row['finished'] else 0
            rd_params = (row['raceid'], row['playerid'], row['time'], row['rank'], row['igt'], row['comment'], level,)
            db_new.execute('INSERT INTO racer_data (race_id, discord_id, time, rank, igt, comment, level) VALUES (?,?,?,?,?,?,?)', rd_params)
            
        db_new.commit()    
    finally:
        db_old.close()
        db_new.close()        

## Transfer data into user_prefs
def transfer_user_prefs():
    db_old = sqlite3.connect('data/users.db')
    db_old.row_factory = sqlite3.Row
    db_new = sqlite3.connect(DB_OUT_NAME)

    try:
        for row in db_old.execute('SELECT * FROM user_prefs'):
            params = (row['playerid'], row['hidespoilerchat'], row['dailyalert'], row['racealert'],)
            db_new.execute('INSERT INTO user_prefs (discord_id, hidespoilerchat, dailyalert, racealert) VALUES (?,?,?,?)', params)

        db_new.commit()     
    finally:
        db_old.close()
        db_new.close()            

##-------------------------

make_new_database()
transfer_daily_data()
transfer_race_data()
transfer_user_prefs()
