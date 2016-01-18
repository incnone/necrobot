# Necrobot TODO

Current version: 0.3.0

## Small improvements

- The `.help` command should make a Discord-mention of the command list channel.
- (?) Add options for setting personal defaults on `.make` (or `.makeprivate`)
- (?) Make race channels vanish for non-admin, non-racer once the race has begun

## Major improvements

### Support for voice rooms attached to race rooms

Create a raceroom command `.addvoice` that attaches a private voice channel to the race channel. 
In a public race, users entering the race could be automatically moved to this voice channel; 
in a private race, both admins and racers will be moved to the channel. The channel
should be destroyed when the race room is destroyed.

### Encapsulate database access, and make "thread-safe"

Currently the bot accesses two databases, daily.db and races.db, which keep track of
the times for the speedrun daily and results of public races. Presumably more will be
added. It does this through sqlite3.

I would like to encapsulate all these accesses in a single class responsible for handling
the databases. One primary objective of doing this is to make these database accesses
"thread-safe" -- by this, I mean that because this program uses asyncio, it's possible
for two coroutines to be accessing the database at the same time, which may cause
problems with sqlite (I am not sure). What is the right way to deal with this? (It's possible
that a simple mutex will do the job fine.)