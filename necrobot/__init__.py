"""
Dependency Tree
---------------
util
    botbase
    database
        user
            race
    vodrecord
    

Modules
-------
config
    Global bot configuration.
exception
    Definition of some custom exception classes.
logon
    Discord logon.


Package summary
-----------------
automatch
    Algorithms for automatic matchmaking.
botbase
    Core classes for the bot's architecture.
condor
    For running condorbot on the CoNDOR Event server.
daily
    For running the various speedrun dailies.
database
    Functions giving database access.
gsheet
    For interacting with a GSheet.
ladder
    For running a 1v1 race ladder.
league
    Holds a "league" variable that determines database schema.
match
    For handling matches, which are sequences of races between two common racers.
necroevent
    Publish-subscribe global event pattern.
race
    Core race functionality.
stats
    For computing stats on race and match data.
stdconfig
    For running necrobot on the Crypt of the Necrobot server.
stream
    For interacting with RTMP streams.
test
    Commands for automating testing within discord.
user
    User data and preference info.
util
    Various utility functions.
"""