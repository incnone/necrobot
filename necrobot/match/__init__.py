"""
A match is a collection of races between exactly two racers. These races share a common private channel, visible to
admins and to the racers, which is used only for this match.


Package Requirements
--------------------
race
    botbase
    database
    util
    user
ladder (TODO - remove)
league (TODO - remove)
gsheet (TODO - remove)


Module Overview
---------------
`Match` is the main data class, and represents a row of the database table `matches`. Because `Match`es interact with
the databse very closely, they should never be created through their constructor. The appropriate factory method is
`matchutil.make_match`. 

A `Match` contains: uIDs for both racers; a MatchInfo; scheduling information; and some other match-related information.

A `MatchInfo` contains a `RaceInfo` (the default race type) as well as the number of races (and whether the match is
a best-of). 

`matchutil` is the factory class, and also contains useful methods for finding collections of matches via the database.
It could probably benefit from a refactor.

`MatchRoom` is the BotChannel associated with running a match.

`MatchRaceData` is a convenience class (more of a struct) for storing data about the set of races in a match. It
roughly corresponds to a row of the database table `match_races`.


Dependencies
------------
cmd_match
    exception
    botbase/
        necroevent
        command
        commandtype
    league/
        leaguemgr
    match/
        matchdb
    user/
        userlib
    util/
        console
        server
        timestr
        parse/
            dateparse
match
    gsheet/
        matchgsheetinfo
    match/
        matchinfo
    race/
        raceinfo
    user/
        necrouser
        userlib
    util/
        console
        decorators
matchdb
    database/
        dbconnect
        dbutil
    match/
        match
        matchracedata
    race/
        racedb
matchfindparse
    exception
    match/
        match
        matchdb
        matchutil
    user/
        userlib
        parse/
            dateparse
matchinfo
    exception
    race/
        raceinfo
    util/
        parse/
            matchparse
matchmgr
    botbase/
        necroevent
        manager
        necrobot
    match/
        matchdb
        matchutil
        matchroom
    util/
        console
        server
        singleton
matchracedata
matchroom
    botbase/
        botchannel
        necroevent
    match/
        cmd_match
        matchdb
        match
        matchracedata
    race/
        cmd_race
        raceinfo
        race
        raceconfig
    user/
        cmd_user
    util/
        console
        ordinal
        server
        timestr
matchutil
    botbase/
        necrobot
    gsheet/
        matchgsheetinfo
    match/
        match
        matchinfo
        matchroom
    race/
        racedb
        raceinfo
    user/
        necrouser
    util/
        console
        timestr
        writechanel
        strutil
        rtmputil
        server
"""