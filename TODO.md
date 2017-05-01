# Necrobot TODO

Current version: 0.10

## Automatching

- Everything
- Auto-register users on match creation

## Ladderbot and Leagues

- Lots of things here
- Better rankings display
- Add match entrants to the `entrants` table in a league database

## Refactor

- Solve circular import Necrobot -> userdb -> NecroUser -> Necrobot
- `util.level.py` and `util.racetime.py` might work better as classes
- Replace NoneType returns with exceptions where appropriate
- Gather argument parsing code

### Cleaner lib classes

- combine MatchRaceData and Match in a friendly way
- better standings update code

### Testing

- Make more small/unit tests (may wish to use a mock DB and/or a mock discord client)

## Bugs
 
### QoL UI Improvements

- Deal with duplicated Discord names in commands like `.add` (allow for discriminator)
- Better timezone parsing
- More friendly parsing of spaces in command arguments

### Unclear issues

- Various issues with raceroom topic not updating properly (e.g. on .r without .e)
- `.forcecancel` is kind of unintuitive when input pre-race, since it's not clear if you want to cancel the race
just finished or the race that people are currently entering. It maybe also doesn't work after a race?

## Features

- Configuration of `.racealert` for character-specific, etc
- Add more complicated sorts to `.mostraces`
- Add `.forceunready` command
- Raceroom-specific voice chat, with an audio countdown and some other audio support (e.g. "Please pause.").

### Different race modes

- Score
- Time limits, with an auto-ping when the time expires

### Stream support / Twitch integration

Allow for users to register their streams and to tag certain races as "streamed". For such races, generate 
a multitwitch or kadgar link upon asking. As an even bigger project, make the bot able to check whether said 
users are actually streaming. Also, make the bot able to report in your twitch chat when people in your race 
have finished or forfeit (and who won, etc.)

### Daily improvements

- A weekly that's intended for optimizing a seed.
- Make the daily more like an asynchronous race: You're allowed to die, and the bot tracks your time between a
`.begin` and `.done` sent via PM. (This could be made alongside an "individual run module" for practicing?)
