"""
Package for managing a ranked ladder, which is a special kind of ongoing League.


Package Requirements
--------------------
botbase
match
stats
user


Dependencies
------------
cmd_ladder
    botbase/
        commandtype
    ladder/
        ratingsdb
    match/
        cmd_match
        matchinfo
    user/
        userlib
ladder
    util/
        server
ladderadminchannel
    botbase/
        botchannel
        cmd_seedgen
    ladder/
        cmd_ladder
    race/
        cmd_racestats
    user/
        cmd_user
rating
ratingsdb
    database/
        dbconnect
    ladder/
        rating
        ratingutil
ratingutil
    ladder/
        rating
    util/
        console
"""