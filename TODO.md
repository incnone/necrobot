# Necrobot TODO

Current version: 0.10

## To be done soon

### Condorbot

- Manual matchup creation
- Automatching
- Deal with HTTP errors (service down) when making requests to the GSheet API
- Rigorously test the user-ID-transferring in database.userdb, since errors could lead to massive losses 
of information
- A lot of unit testing

#### Unimplemented commands:

- `.next`
- `.staff`
- `.dropracer`
- `.fastest`, `.stats` 
- `.contest`
- Commands I won't re-implement:  `.remind`, `.forcetransferaccount`, `.updategsheetschedule`, `.updatecawmentary`,
`.register`, `.cancel`, `.forcerecordmatch`

### Ladderbot

- Automatch feature
- Better rankings display

### Other

- Uniformize and improve argument parsing
- Create unit tests for all modules

## Bugs

### Fixable/precise but not urgent

- `.dailywhen` is not working as advertised.
- Deal with duplicated Discord names in commands like `.add`
 
### Vague or not urgent

- More friendly parsing of spaces in command arguments
- Various issues with raceroom topic not updating properly (e.g. on .r without .e)
- Daily leaderboards will break due to post length if more than ~45 people participate
- It's technically possible for the daily seed to be the same as a previous seed

### Unclear sort-of-buggy behavior

- `.forcecancel` is kind of unintuitive when input pre-race, since it's not clear if you want to cancel the race
just finished or the race that people are currently entering. It maybe also doesn't work after a race?
- `.notify off` followed by `.e` causes the user to be on the notify list, which may be unintuitive.

## Features

- Make `.notify on` do the obvious thing
- add comment possibility to `.death`
- fix `.d 1-3` (and the like) causing race finish
- add more complicated sorts to `.mostraces`
- add `.forceunready` command
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
