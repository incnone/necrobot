# Necrobot TODO

Current version: 0.10

## Current TODO

### General
- Make condorbot/necrobot not overwrite each other's/their own logging files
- Replace NoneType returns with exceptions where appropriate
- Output text in channel when a command throws an error (if possible)
- Fix frequent caching errors
- Better handling of rate-limiting issues on countdown (fix delay before 'Go!' text)
- Add admin command to delete racerooms (for remaking), instead of just closing them

### Dependencies
- Split race/match stats dependencies into appropriate packages 
- Remove `stats` dependency from `ladder` (perhaps split into a "ratings" and "ladder" package?)
- Clarify `league` dependency in `ladder`?
- Remove `league` from `cmd_match`:
    Currently `.suggest` looks at the league deadline to determine if the given time is appropriate. How to fix this?
    Could give matches their own per-match deadline, but then need to carefully update it when the deadline changes
    after matches are made. Perhaps better would be to possibly associate a League to each Match? Ideal might be to
    use the Event system ("I am trying to schedule a match for X, is that okay?").
- Remove `gsheet` from `match` and `matchutil`:
    This will happen naturally with the change to record match ID into the GSheet, so that the GSheet has the data for
    which match is which, instead of the matches having data for where they are on the GSheet.

### League
- Discord category limit is 50, so implement proper workaround when making >50 race rooms

### GSheet
- Give the bot a command to set up a GSheet from blank
- Tag input with match ID on creation, so we don't depend on row/sheetID for identification
- Better standings update code

### Match
- Make bot say races awaiting review in match score announcement when contested races
- Remove or notify commentator on match reschedule
- combine MatchRaceData and Match in a friendly way

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

### Things I don't understand

- manfred4 wasn't properly added to rooms on RTMP setting; traceback was:
  File "/home/bot/necrobot/necrobot/match/matchmgr.py", line 41, in ne_process
    overwrite=read_perms
  File "/home/bot/.pyenv/versions/3.5.2/lib/python3.5/site-packages/discord/client.py", line 3040, in edit_channel_permissions
    raise InvalidArgument('target parameter must be either Member or Role')
- Ri's timezone was getting read as none by bot but correctly used

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
