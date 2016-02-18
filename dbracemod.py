import codecs
#import config
import sqlite3

DB_NAME = 'data/necrobot.db'
TEXTFILE_NAME = 'data/races.txt'

f = open(TEXTFILE_NAME, 'r')
db_conn = sqlite3.connect(DB_NAME)

db_conn.execute("ALTER TABLE race_data RENAME TO temp_race_data")
db_conn.execute("ALTER TABLE racer_data RENAME TO temp_racer_data")

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


class Racer(object):
    def __init__(self):
        self.discord_id = 0
        self.time = 0
        self.rank = 0
        self.igt = 0
        self.comment = ''
        self.level = 0

def is_date_str(string):
    return string.startswith('January')

def is_header_str(string):
    return len(string) > 3 and (string[1] == ':' or string[2] == ':')

def is_seed_str(string):
    return string.startswith('Seed:')

def parse_header_str(header_str):
    args = header_str.split()
    if not len(args) == 12:
        print('Error parsing header <{}>.'.format(header_str))
        exit(-1)

    day = int(args[7])    
    utc_time_strs = args[11].split(':')
    utc_hr = int(utc_time_strs[0])
    utc_min = int(utc_time_strs[1])

    timestamp = '2016-01-{0} {1}:{2}:00'.format(day, utc_hr, utc_min)
    return timestamp

def parse_type_str(type_str):
    args = type_str.split()
    arglen = len(args)
    assert args[arglen - 1] == 'Seeded' or args[arglen - 1] == 'Unseeded'
    
    char = args[0]
    seeded = (args[arglen - 1] == 'Seeded')
    custom_str = ''
    if arglen != 2:
        for i in range(1, arglen - 1):
            custom_str += args[i]
    if not custom_str:
        custom_str = 'All-zones'

    return [char, seeded, custom_str]

def get_seed(seed_str):
    args = seed_str.split()
    assert len(args) == 2
    return int(args[1].rstrip('\n'))

def get_time_str(string):
    time_split = string.split(':')
    min_split = time_split[1].split('.')
    ts = [time_split[0], min_split[0], min_split[1].rstrip('):')]
    return 6000*int(ts[0]) + 100*int(ts[1]) + int(ts[2])    

def parse_racer_str(racer_str, rank):
    racer = Racer()
    racer.rank = rank
    racer_str = racer_str[5:]
    args = racer_str.split()

    params = (args[0],)
    for row in db_conn.execute('SELECT discord_id FROM user_data WHERE name=?', params):
        racer.discord_id = int(row[0])

    forfeit = args[2].startswith('Forfeit')
    racer.time = 0 if forfeit else get_time_str(args[2])
    racer.level = 0 if forfeit else 18
    racer.igt = -1
    start_comment_at = 3
    if len(args) > 4 and args[3] == '(igt':
        racer.igt = get_time_str(args[4])
        start_comment_at = 5

    racer.comment = ''
    for i in range(start_comment_at, len(args)):
        racer.comment = racer.comment + args[i] + ' '
    if racer.comment:
        racer.comment = racer.comment[:-1]

    return racer

def insert_race(raceid, header_str, type_str, seed, racer_strs):
    timedata = parse_header_str(header_str)
    racedata = parse_type_str(type_str)
    char = racedata[0]
    seeded = racedata[1]
    flags = int(1) if seeded else int(0)
    custom = racedata[2]
    racers = []
    rank = 0
    for racer_str in racer_strs:
        rank += 1
        racers.append(parse_racer_str(racer_str, rank))

    params = (raceid, timedata, char, custom, flags, seed,) 
    db_conn.execute('INSERT INTO race_data (race_id, timestamp, character, descriptor, flags, seed) VALUES (?,?,?,?,?,?)', params)
    for racer in racers:
        params = (raceid, racer.discord_id, racer.time, racer.rank, racer.igt, racer.comment, racer.level,)
        db_conn.execute('INSERT INTO racer_data (race_id, discord_id, time, rank, igt, comment, level) VALUES (?,?,?,?,?,?,?)', params)   

def insert_old_races():
    raceid = 0
    header_str = f.readline()
    end = False
    while True:
        if end:
            break
        
        type_str = f.readline()
        racer_strs = []
        seed = 0

        while True:
            next_line = f.readline()
            
            if is_date_str(next_line):
                next_line = f.readline()
                
            if not next_line or is_header_str(next_line):
                insert_race(raceid, header_str, type_str, seed, racer_strs)
                raceid += 1
                header_str = next_line
                racer_strs = []
                if not next_line:
                    end = True
                break
            elif is_seed_str(next_line):
                seed = get_seed(next_line)
            else:
                racer_strs.append(next_line)

    return raceid

def copy_new_races(race_offset):
    for row in db_conn.execute('SELECT * FROM temp_race_data'):
        params = (int(row[0]) + race_offset, row[1], row[2], row[3], int(row[4]), int(row[5]),)
        db_conn.execute('INSERT INTO race_data VALUES (?,?,?,?,?,?)', params)
    for row in db_conn.execute('SELECT * FROM temp_racer_data'):
        params = (int(row[0]) + race_offset, int(row[1]), int(row[2]), int(row[3]), int(row[4]), row[5], int(row[6]),)
        db_conn.execute('INSERT INTO racer_data VALUES (?,?,?,?,?,?,?)', params)
    

copy_new_races(insert_old_races())
db_conn.execute("DROP TABLE temp_race_data")
db_conn.execute("DROP TABLE temp_racer_data")
db_conn.commit()
db_conn.close()
