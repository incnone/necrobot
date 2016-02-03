# Necrobot TODO

Current version: 0.4.0

## Small changes

- Daily leaderboards will break due to post length if more than ~45 people participate; fix
- Ensure that the daily seed is different from the previous seed
- Allow the race creator to change the race rules after creating the room. 
- Replace lists with sets where appropriate

### Different race modes

- Best-of-x or repeat-y-times races (mostly for CoNDOR purposes)
- Score
- Flagplanting
- Sudden death
- Last man standing (?)

### Possiblilites to consider (not sure I want these yet)

- Add top daily times to spoilerchat topic
- Allow for people to set/store raceroom rules, so one can call e.g. `.setrules 4shrine` at the beginning of a race, and then people can call `.rules` to get the rules for the current race
- Add a race mode where the victor is determined by a race admin, rather than times/etc.
- If a user has two seeds active and both are submittable, force them to use a `-date` flag for their submission. (This should work like `-date Jan20`.) In general, allow use of the `-date` flag for daily submission, giving an error if the user inputs a date that isn't their most recent seed.
- Add options for setting personal defaults on `.make` (or `.makeprivate`)
- Add hyperlinks to daily leaderboard times, so people can link vods/screenshots (I don't know how to do this and keep the nice formatting at the moment.)
- Add comments to daily leaderboards, visible by hovering over them or something like that. (Again, I don't know how this could be done in Discord at the moment. Actually displaying the comments likely takes up too much screen real-estate.)
- Properly bugfix for when the bot is subscribed to multiple servers. (Calls like client.get_all_channels should be rewritten. This may also require a refactor. I'm not actually sure what the use case is for this at the moment, so it's hard to see exactly how the code should be written to support it.)
- Capture all text in a race channel when it's closed, and save it somewhere.

## Major feature improvements

### Database search & statistics; ratings based on daily/race rankings

Implement a module for getting statistics for a user from races, dailies, etc. 

Implement some algorithms for ranking people based on daily performance (and participation) and race performance (and participation), much like the NecroLab power rank and SRL ranks. (These are two separate ranks.) 

### Individual run module

Add a module accessable via PM that allows a user to store and track individual runs (e.g. for practice), and then later get stats on those runs.

### Support for voice rooms attached to race rooms

Might be nice to have the ability to make raceroom-specific voice chat, but I'm unsure of how to improve upon the current system of just having a stable voice chat. The point is that it's silly to be changing voice chat between races or to only allow racers into voice chat. So is there really any functionality here that's missing? This would probably be more of a feature you'd want if Necrobot gets integrated into the main Necrodancer Discord.

### Encapsulate database access, and make "thread-safe"

Currently the bot accesses two databases, daily.db and races.db, which keep track of the times for the speedrun daily and results of public races. Presumably more will be added. It does this through sqlite3.

I would like to encapsulate all these accesses in a single class responsible for handling the databases. One primary objective of doing this is to make these database accesses "thread-safe" -- by this, I mean that because this program uses asyncio, it's possible for two coroutines to be accessing the database at the same time, which may cause problems with sqlite (I am not sure). What is the right way to deal with this? (It's possible that a simple mutex will do the job fine.) So far this hasn't been a problem; unfortunately I'm ignorant of how much this 'ought to' be a problem because I'm still hazy on the exact details of how asyncio -- and, for that matter, sqlite3 -- work.

### Stream support / Twitch integration

Allow for users to register their streams and to tag certain races as "streamed". For such races, generate a multitwitch or kadgar link upon asking. As an even bigger project, make the bot able to check whether said users are actually streaming. Also, make the bot able to report in your twitch chat when people in your race have finished or forfeit (and who won, etc.)

### Support for best-of-x or repeat-y-times races

Add support to private race rooms for matches to be played best-of-x (when two racers only, presumably) or repeat-y-times. The race room should remain the same for all matches and should keep track of the current match score, and results should be reported as one match. The main purpose of this is for CoNDOR Season 4, when repeat-3-times will be the standard.

### Support for an optimized speedrun daily

Add a daily that's intended for optimizing a seed. May also want to consider adding dailies for other categories as well. The main difficulty here is figuring out how to organize things from a UI perspective, rather than writing the code.
