# Necrobot TODO

Current version: 0.13

## Current TODO

### General
- Replace NoneType returns with exceptions where appropriate
- More efficient database requests (especially on Condorbot startup)
- Do assignment into leagues via role assignment

### GSheet
- Drastically simplify GSheet interaction (full overwrite updates, no reading from sheet)

### Match
- Make bot say races awaiting review in match score announcement when contested races
- Remove or notify commentator on match reschedule
- Combine MatchRaceData and Match in a friendly way

### Util
- `util.level.py` and `util.racetime.py` might work better as classes, when wanting to generalize to other games

### Parsing
- More consistent/flexible command-line syntax
- Better public-facing command-line documentation (i.e. `.help` command)
- Deal with duplicated Discord names in commands like `.add` (allow for discriminator)
- More friendly parsing of spaces in command arguments

### Testing
- Make more small/unit tests (may wish to use a mock DB and/or a mock discord client)

## Bugs
- `.d 2-3` responds with '<player> has forfeit the race' twice
- `.register-condor-event` should do more to set up convenient views in database
- Necrobot and Condorbot should not attempt to write to the same log file
- Fix identical times causing a racer to be listed twice on `.fastest`

### Unclear issues
- `.forcecancel` doesn't seem to work as intended; racerooms can get stuck
- Various issues with raceroom topic not updating properly (e.g. on .r without .e)
- `.forcecancel` is kind of unintuitive when input pre-race, since it's not clear if you want to cancel the race
just finished or the race that people are currently entering. It maybe also doesn't work after a race?

## Possible features (no concrete plans to implement these)

- Raceroom-specific voice chat, with an audio countdown and some other audio support (e.g. "Please pause.").
- Configuration of `.racealert` for character-specific, etc

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
