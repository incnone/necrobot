"""
A race is the core unit of Necrobot functionality. A race is a number of discord users, its racers, playing the game
in tandem. Typically the goal is to finish a specific task (e.g. the game) as fast as possible, but support is planned
for less time-based taskes (such as score runs), which will likely use much of the code in this module. At the end of
a race the racers are ranked in some fashion and their results recorded to the necrobot's MySQL database.

`race`.`Race` is the class representing the race itself. Information about `Race` objects is recorded to the databse 
when races are finalized, to the table `races`, but there is not a 1-1 correspondence with database information (unlike 
in the case of `Match`, `League`, and `NecroUser`). A `Race` object is run under the auspice of some `parent`, passed 
to its constructor; a `parent` is an abstract interface which implements the coroutines `process`, for processing 
`RaceEvent`s, and `write`, for outputting text that the racers can see.

The currently implemented `Race` parent classes are `race.publicrace.raceroom`, `race.privaterace.privateraceroom`, and
`match.matchroom`. (Note that these are all BotChannels, which is not strictly required but is the design I have in
mind.)

`race`.`RaceEvent` is a class representing events that can happen during a race (e.g. RACE_END, RACER_FINISH). This is
so that various parent-type objects can react to such events. The `RaceEvent` pattern is Observer-Subject, in contrast
to the Publish-Subscribe pattern used in the `necroevent` sub-package.

`Racer` represents an individual racer in some particular race. It thus contains data like finish time or death level.
The data from this class is written to the `race_runs` table when the race is finalized.

`RaceInfo` stores information about the type of race; much of this information is itself stored in `race_types`, and
the rest in `races`. (Which table it's stored in depends on how race-specific the information is; for instance, seeds
are stored in `races`, but whether a race is seeded is part of the "type" of a race, which is stored in `race_types`.)

`RaceConfig` stores information about the variables in the way races are run (countdown length, time between completion
and recording, whether to auto-forfeit the last racer when all others have finished).

`racetime` has functions for converting different time-data storage (ints as hundredths of a second and XX:XX.xx 
format).

`cmd_race` and `cmd_racemake` have typical race-related commands.
"""
