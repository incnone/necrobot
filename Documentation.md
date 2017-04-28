# Necrobot sort-of documentation (v 0.10)

## Notes on large-scale organization

`necrobot.util` modules are only allowed to `import` from other `necrobot.util` modules. These serve
simple, generic, package-wide utility functions. (In certain places, `util` modules could likely use
some refactoring.) However, there are many utility-like modules in other sub-packages.

In general, modules implementing derived  classes of `BotChannel` are highest-level. These should
be added to the necrobot via an out-of-package function; see `botconfigs.py`.

`BotChannel` modules import `cmd_*` classes to achieve their various functions. The `cmd_*` classes
give implementations of various `CommandType` objects.

A `CommandType` object is intended to deal with the UI involved in interpreting a `Command`. In
its `_do_execute` method, it should parse the user's input (handling bad input if necessary). It
passes data-manipualtion work off to an object representing such data or a `*util` module, but should
catch exceptions related to parsing this data when appropriate and display a relevant message in the
command channel.

## Notes on the Race module

(TODO)

## List of database-based objects

Objects in this list are meant to be local representations of various kinds of database information.

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