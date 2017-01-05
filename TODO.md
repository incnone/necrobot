# Necrobot TODO

Current version: 0.6.1

## Known bugs

### Fixable/precise but not urgent

- `.missing` command appears to be broken; not sure what the conditions for this are.
- Make `.dailyseed` available in necrobot_main channel
- Race rooms aren't being closed after appropriate time
- `.poke` is not working. [maybe fixed]
- `.dailywhen` is not working as advertised.
 
### Vague or not urgent

- Various issues with raceroom topic not updating properly (e.g. on .r without .e)
- Daily leaderboards will break due to post length if more than ~45 people participate
- It's technically possible for the daily seed to be the same as a previous seed

## Unclear sort-of-buggy behavior

- `.forcecancel` is kind of unintuitive when input pre-race, since it's not clear if you want to cancel the race
just finished or the race that people are currently entering.
- `.notify off` followed by `.e` causes the user to be on the notify list, which may be unintuitive.

## Features

- add `.forceunready` command

### Different race modes

- Score
- Time limits, with an auto-ping when the time expires

### Support for matches

It should be simple to make a "best-of-X" or "repeat-Y" type of "private match" in the bot. This is mostly for CoNDOR purposes.

### Support for voice rooms attached to race rooms

Raceroom-specific voice chat, with an audio countdown and some other audio support (e.g. "Please pause.").

### Stream support / Twitch integration

Allow for users to register their streams and to tag certain races as "streamed". For such races, generate a multitwitch or kadgar link upon asking. As an even bigger project, make the bot able to check whether said users are actually streaming. Also, make the bot able to report in your twitch chat when people in your race have finished or forfeit (and who won, etc.)

### Daily improvements

- A weekly that's intended for optimizing a seed.
- Make the daily more like an asynchronous race: You're allowed to die, and the bot tracks your time between a
`.begin` and `.done` sent via PM. (This could be made alongside an "individual run module" for practicing?)
