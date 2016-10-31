# Necrobot TODO

Current version: 0.6.0

## Necrobot discord server changes

- Remove spoilerchat channels
- Merge daily leaderboard channels
- Change config file to reflect the changes in config.Config

## Known bugs

- Daily leaderboards will break due to post length if more than ~45 people participate
- It's technically possible for the daily seed to be the same as a previous seed

## Features

### Different race modes

- Score
- Flagplanting
- Sudden death

### Support for matches

It should be simple to make a "best-of-X" or "repeat-Y" type of "private match" in the bot. This is mostly for CoNDOR purposes.

### Individual run module

Allow a user to store and track individual runs (e.g. for practice), and then later get stats on those runs.

### Support for voice rooms attached to race rooms

Raceroom-specific voice chat, with an audio countdown and some other audio support (e.g. "Please pause.").

### Stream support / Twitch integration

Allow for users to register their streams and to tag certain races as "streamed". For such races, generate a multitwitch or kadgar link upon asking. As an even bigger project, make the bot able to check whether said users are actually streaming. Also, make the bot able to report in your twitch chat when people in your race have finished or forfeit (and who won, etc.)

### Daily improvements

- A weekly that's intended for optimizing a seed.
- Make the daily more like an asynchronous race: You're allowed to die, and the bot tracks your time between a
`.begin` and `.done` sent via PM.
