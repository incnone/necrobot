"""
Core classes for the bot.

Package Requirements
--------------------
    util


Module Overview
---------------
botchannel
    BotChannel: Represents a Discord channel in which the bot can receive commands.

cmd_admin
    Broad-use admin-only commands.

cmd_all
    Commands that should be included in every BotChannel.

command
    Command: Represents a full user command input (e.g. `.make -c Cadence -seed 12345 -custom 4-shrine`)

commandtype
    CommandType: Abstract Base Class representing a command that the user can call (e.g. `.make`)

discordutil
    Utility methods for interacting with discord.

manager
    Manager: Abstract Base Class. A Manager does loading and event handling for some specific RaceBot functionality.
    
necrobot
    Necrobot: Singleton class containing core global Necrobot data.
    
server
    Module containing global data representing the Discord server on which this bot is running, as well as the
    discord.Client object.
    

Dependencies
------------
botchannel
    config
cmd_admin
    exception
    botbase/
        commandtype
        necrobot
cmd_all
    config
    botbase/
        commandtype
        necrobot
    util/
        server
cmd_color
    botbase/
        commandtype
    util/
        server
cmd_role
    botbase/
        commandtype
    util/
        server
cmd_seedgen
    botbase/
        commandtype
    util/
        necrodancer/
            seedgen
command
    config
commandtype
    config
    botbase/
        command
        necrobot
    util/
        console
        server
manager
necrobot
    config
    botbase/
        command
        manager
        server
    util/
        console
        singleton
necroevent
    util
server
    config
"""