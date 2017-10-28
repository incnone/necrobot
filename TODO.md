# Necrobot TODO

Current version: 0.10

## Database

- Standardize creation of views when creating a new event
- Clean up "library" classes, which should solve some bugs
- Combine MatchRaceData and Match in a friendly way
- Better standings update code

## Bugs

- Fix issues related to mass canceling of match countdowns
- Allow quoted user names in `.force` command
- Fix bugs with `.makematches` being called mid-week (e.g. blank lines on sheet)
- `.d 2-3` responds with '<player> has forfeit the race' twice
- Identical fastest times causes two listings on `.fastest` (Necrobot)

## Error handling

- Fix UnicodeEncodeErrors on logging write
- Output text in channel when a command throws an error if possible
- Necrobot and Condorbot should not attempt to write to the same log file

## Parsing / UI handling

- Fix help text for `.make` and allow `--` prepended to command keywords
- Deal with duplicated Discord names in commands like `.add` (allow for discriminator)
- Deal with database out-of-date names in commands like `.add`
- Better timezone parsing
- More friendly parsing of spaces in command arguments

## Awaiting something

- Update to use channel groups (Need to wait on discord.py updates)

## Condorbot

### UI touchups

- Make bot say races awaiting review in match score announcement when contested races
- Better information directly on #schedule?
- Race pausing shouldn't alert forfeit or finished racers

### Cawmentary

- Separate table to support putting co-commentators in database
- Give cawmentator read access to race room on match start
- Remove commentator on match reschedule
- PM people who want it if there are uncawmentated races starting in 15 mins?

## Refactor

- `util.level.py` and `util.racetime.py` might work better as classes
- Replace NoneType returns with exceptions where appropriate
- Gather argument parsing code

## Testing

- Make more small/unit tests (may wish to use a mock DB and/or a mock discord client)

## Unclear issues

- `.forcecancel` doesn't seem to work as intended; racerooms can get stuck
- Various issues with raceroom topic not updating properly (e.g. on .r without .e)
- `.forcecancel` is kind of unintuitive when input pre-race, since it's not clear if you want to cancel the race
just finished or the race that people are currently entering. It maybe also doesn't work after a race?

## Nice features, but probably not doing these

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
