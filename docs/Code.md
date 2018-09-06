# Necrobot sort-of documentation (v 0.10)

## Notes on large-scale organization

The core code to run races is contained in the following packages, each of which depends only on the prior
packages in the list:

- `util`
- `botbase` and `database`
- `user`
- `race`

The core league-running code (for the CoNDOR Event server) is contained in `match` and `league`, which depend on all
of the above (and currently have some very minor cross-dependency between them). 

The CoNDOR event server works with a GSheet to input and display match information. The code for this is contained
within the `gsheet` package.

The high-level code determining the actual functionality of Necrobot is contained in `stdconfig`, and the analagous
code for Condorbot is contained in `condor`.

Precise package dependencies are documented in each package's `__init__.py` file.

## Notes on how a specific bot is made from this code

Condorbot is run from `run_condorbot.py`, and Necrobot from `run_necrobot.py`. The code implementing these bots
is contained primarily in `condor` and `stdconfig`, respectively. These files (`run_*.py`) typically do the following
things:
- Register a "main" BotChannel object with the Necrobot singleton, which is the primary place the bot gets commands.
This defines the primary bot functionality. These objects are typically little more than lists of commands; you can see
examples in `condor.condormainchannel.py` (for Condorbot) and `stdconfig.mainchannel.py` (for Necrobot).
- Register a "PM" BotChannel object, which is similar to the main channel, but instead of being associated with a
particular discord channel on the bot's server, this object lists the commands accessible through PM.
- Optionally register other channels for command input, like Condorbot's "admin" channel where races are made. (Note
that channels created by the bot, like individual race rooms, are not registered in these `run_*.py` files.)
- Optionally register an event listener (a "Manager" object) to respond in particular ways to bot events. (See 
`condor.condormgr.py` for an example.)

The `BotChannel` classes defined above import `cmd_*` modules to achieve their various functions. The `cmd_*` modules
give implementations of various `CommandType` objects. A `CommandType` object is intended to deal with the UI involved
in interpreting a `Command`. In its `_do_execute` method, it should parse the user's input (handling bad input if 
necessary). It passes data-manipualtion work off to an object representing such data or a `*util` module, but should
catch exceptions related to parsing this data when appropriate and display a relevant message in the
command channel.

## List of database-based objects

Objects in this list are meant to be local representations of rows in various tables of the database (the table 
depending on object type).

### `ladder.rating`

- `Rating` : User rating data. DB: `necrobot.ladder_data`.

### `race.match`

- `match.Match` : Data for a match. DB: `necrobot.match_data`.
- `matchracedata.MatchRaceData` : Race data associated to a match;. DB: `necrobot.match_races`.

### `race`

- `raceinfo.RaceInfo` : Information about the type of race. DB: `necrobot.race_types`.
- `racer.Racer` : A single racer in a single race. DB: `necrobot.racer_data`.
- `race.Race` : A single race. DB: `necrobot.race_data`.

### `user.necrouser`

- `NecroUser` : A bot user. DB: `necrobot.user_data`.