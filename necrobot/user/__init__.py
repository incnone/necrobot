"""
User data.


Package Requirements
--------------------
botbase (for cmd_user only)
database
necroevent (for cmd_user only)
util


Description
-----------
cmd_user
    CommandType classes for manipulating user data.
    
necrouser
    NecroUser: Class representing a RaceBot user.
    
userlib
    Module for caching database information for RaceBot users.
    
userprefs
    Struct containing user-specific preferences.
    

Dependencies
------------
cmd_user
    botbase/
        command
        commandtype
    necroevent/
        necroevent
    user/
        necrouser
        userlib
        userprefs
    
necrouser
    user/
        userprefs
    util/
        console
        server
        strutil
        
userdb
    database/
        dbconnect
    user/
        necrouser
        userprefs
    util/
        console    
       
userlib
    exception
    database/
        userdb
    user/
        necrouser
        userprefs
    util/
        console
        server

userprefs
"""