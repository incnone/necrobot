# Necrobot TODO

Current version: 0.3.4

## Small changes

- Daily leaderboards will break due to post length if more than ~45 people participate; fix
- Ensure that the daily seed is different from the previous seed
- Allow the race creator to change the race rules after creating the room. 
- Mark the time of forfeit, and add the option to input death level (e.g. `.death 4-3`)
- Add a command for viewing current user preferences
- Replace lists with sets where appropriate

### Different race modes

- Best-of-x or repeat-y-times races (mostly for CoNDOR purposes)
- Score
- Flagplanting
- Sudden death

### Possiblilites to consider (not sure I want these yet)

- Allow for people to set/store raceroom rules, so one can call e.g. `.setrules 4shrine` at the beginning of a race, and then people can call `.rules` to get the rules for the current race
- Add a race mode where the victor is determined by a race admin, rather than times/etc.
- If a user has two seeds active and both are submittable, force them to use a `-date` flag for their submission. (This should work like `-date Jan20`.) In general, allow use of the `-date` flag for daily submission, giving an error if the user inputs a date that isn't their most recent seed.
- Add options for setting personal defaults on `.make` (or `.makeprivate`)
- Add hyperlinks to daily leaderboard times, so people can link vods/screenshots (I don't know how to do this and keep the nice formatting at the moment.)
- Add comments to daily leaderboards, visible by hovering over them or something like that. (Again, I don't know how this could be done in Discord at the moment. Actually displaying the comments likely takes up too much screen real-estate.)
- Properly bugfix for when the bot is subscribed to multiple servers. (Calls like client.get_all_channels should be rewritten. This may also require a refactor. I'm not actually sure what the use case is for this at the moment, so it's hard to see exactly how the code should be written to support it.)
- Capture all text in a race channel when it's closed, and save it somewhere.

## Major feature improvements

### Support for voice rooms attached to race rooms

Create a raceroom command `.addvoice` that attaches a private voice channel to the race channel. In a public race, users entering the race could be automatically moved to this voice channel; in a private race, both admins and racers will be moved to the channel. The channel should be destroyed when the race room is destroyed.

### Encapsulate database access, and make "thread-safe"

Currently the bot accesses two databases, daily.db and races.db, which keep track of the times for the speedrun daily and results of public races. Presumably more will be added. It does this through sqlite3.

I would like to encapsulate all these accesses in a single class responsible for handling the databases. One primary objective of doing this is to make these database accesses "thread-safe" -- by this, I mean that because this program uses asyncio, it's possible for two coroutines to be accessing the database at the same time, which may cause problems with sqlite (I am not sure). What is the right way to deal with this? (It's possible that a simple mutex will do the job fine.) So far this hasn't been a problem; unfortunately I'm ignorant of how much this 'ought to' be a problem because I'm still hazy on the exact details of how asyncio -- and, for that matter, sqlite3 -- work.

### Database search & statistics; ratings based on daily/race rankings

Implement some algorithms for ranking people based on daily performance (and participation) and race performance (and participation), much like the NecroLab power rank and SRL ranks. (These are two separate ranks.) 

### Stream support / Twitch integration

Allow for users to register their streams and to tag certain races as "streamed". For such races, generate a multitwitch or kadgar link upon asking. As an even bigger project, make the bot able to check whether said users are actually streaming. Also, make the bot able to report in your twitch chat when people in your race have finished or forfeit (and who won, etc.)

### Support for best-of-x or repeat-y-times races

Add support to private race rooms for matches to be played best-of-x (when two racers only, presumably) or repeat-y-times. The race room should remain the same for all matches and should keep track of the current match score, and results should be reported as one match. The main purpose of this is for CoNDOR Season 4, when repeat-3-times will be the standard.

### Support for an optimized speedrun daily

Add a daily that's intended for optimizing a seed. May also want to consider adding dailies for other categories as well. The main difficulty here is figuring out how to organize things from a UI perspective, rather than writing the code.

## Refactoring

### A skeleton bot with attachable "modules"

Something that seems like a nice way to refactor the code would be to make necrobot.py into a skeleton to which we can attach "modules", of which we would currently have two: the "racing" module and the "daily" module. Each module would be independently responsible for handling commands, writing to the main channel, etc; we could put a lot of the stuff in main.py into necrobot.py (maybe, though I hate combining modules), and move the specific handling of commands to the modules. This would help for the future, when we want to make a necrobot for season 4, which should have something like (but not identical to) the current race functionality, but nothing like the daily functionality.

### Easier ways to get at channels, server

Right now we're passing around a lot of random discord objects (client, server, etc) when we have a specific design pattern in mind: a bot functioning on a single server, with particular dedicated channels. It'd be nice to do this in a somewhat cleaner way, so that we're not forced to do things like call `client.get_all_channels()` and then search the returned list for a channel matching a particular string.

### Most commands accessible via PM

Most non-race commands, like setting user preferences, etc, should be accessible through PM. From a coding standpoint, I think it makes sense to have a "Command" class such that imputs to the bot are parsed and become instances of this class; Command will have e.g. a "command" field and a list of "args" that can be easily read, as well as carrying around the message object used to call the command (for access to message.author, message.channel, and message.content). Parsing the command into a command and args should happen very abstractly, before the command is seen by any module. Then presumably we should have some system for determining which modules handle a given command (perhaps every module just looks at every command, and makes its own decisions based on the channel and command).
