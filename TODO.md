# Necrobot TODO

Current version: 0.3.0

## Small improvements

- If a user has two seeds active and both are submittable, force them to use a `-date` flag for their
submission. (This should work like `-date Jan20`.)
- In general, allow use of the `-date` flag for daily submission, giving an error if the user inputs
a date that isn't their most recent seed.

### Possiblilites to consider (not sure I want these yet)

- (?) Add options for setting personal defaults on `.make` (or `.makeprivate`)
- (?) Make race channels vanish for non-admin, non-racer once the race has begun
- (?) Add hyperlinks to daily leaderboard times, so people can link vods/screenshots (I don't know
how to do this and keep the nice formatting at the moment.)
- (?) Add comments to daily leaderboards, visible by hovering over them or something like that. (Again,
I don't know how this could be done in Discord at the moment. Actually displaying the comments likely
takes up too much screen real-estate.)

## Major improvements

### Support for best-of-x or repeat-y-times races

Add support to private race rooms for matches to be played best-of-x (when two racers only, presumably)
or repeat-y-times. The race room should remain the same for all matches and should keep track of the
current match score, and results should be reported as one match.

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

### Stream support / Twitch integration

Allow for users to register their streams and to tag certain races as "streamed". For such races,
generate a multitwitch or kadgar link upon asking. As an even bigger project, make the bot able to
check whether said users are actually streaming. Also, make the bot able to report in your twitch chat
when people in your race have finished or forfeit (and who won, etc.)