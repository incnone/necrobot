# Necrobot TODO

Current version: 0.2.3

## Small improvements

- Update the leaderboard when a user is kicked
- The `.help` command should make a Discord-mention of the command list channel.
- (?) Add options for setting personal defaults on `.make` (or `.makeprivate`)
- (?) Make race channels vanish for non-admin, non-racer when the race has begun

## Major features

### Private racerooms

Implement a main-chat command, `.makeprivate`, which makes a restricted-access room.
The parameters to this command would be
```
.makeprivate [char | -c char] [s|u|-s|-u] [-a adminname...] [-r racername...] [-bestof x | -repeat y] [-seed num] [-custom text] 
```
If the command caller is not found among racername..., then the command caller is
automatically made a race admin for that race. 

Calling this command creates a race room which is unreadable except by server admins,
race admins, and racers. (Note: "racers" are users that can see the room. They are automatically
entered into the race. Admins can also enter the race, but this is not automatic.) Racers in a private 
room have the same commands as in a public room. Race admins (as well as server admins) can use the 
following additional commands:
```
Always:
 .remove racername...
 .forcecancel
Before the race:
 .changerules [char | -c char] [s|u|-s|-u] [-bestof x | -repeat y] [-seed num] [-custom text] 
 .invite racername...
 .admin adminname...
 .reseed
 .ready
During the race:
 .pause
 .unpause
 .forcereset
After the race:
 .forcereset
 .rematch
```
Brief explanation of the not completely obvious commands: `.invite` gives users permission to view
the room and enter the race. `.admin` makes users into race admins. `.reseed` generates a new seed for 
the race, if the race is seeded. `.ready` tells the bot that the admin is ready for the race to begin.
(When all admins and racers are ready, the race will begin.) `.forcereset` cancels the race, causing no 
results to be recorded, and resets the race. `.forcecancel` simply cancels the race. `.rematch` records 
the race and begins a new race in the same room with the same admins, racers, and rules. (This differs 
from the public room `.rematch` in that it does not create a new room.)

### Support for 'tourney' races. 

The exact details are not clear, but one idea would be to make a command `.condor`
such that calling `.condor [racer1] [racer2]` makes a private raceroom according to
a preset configuration (which certain Admins could set). For instance, CoNDOR S3 races 
were Cadence unseeded race-3-times, and they would need to happen in private rooms. 
It would be easier and less error-prone for racers to type 
```
.condor [racer1] [racer2]
```
than
```
.makeprivate -racers [racer1] [racer2] -u -repeat 3
```
A command like this could also record races in a separate database, and in a separate
record channel, for easier lookup later. Being able to tag the specific races that are
for the tournament would make doing other database thigns to them possible.

It would be nice to do this in a similar way to the CF/DD bot, where staff can place users
in a private voice room (since this is easy to do with the discord API), and then the bot
can automatically generate a race room that's private to staff + users in the voice channel.

### Support for voice rooms attached to race rooms

Create a raceroom command `.addvoice` that attaches a private voice channel to the race channel. 
In a public race, users entering the race could be automatically moved to this voice channel; 
in a private race, both admins and racers will be moved to the channel. The channel
should be destroyed when the race room is destroyed.

## Major code improvements

### RaceRoom class

Create a class RaceRoom handling the channel-related functionality of Race,
and keep the race-related functionality in Race. This should assist in the 
coding of "private" race rooms, for which the race-related code should be identical
but the channel-related code may be different (and, need to keep list of admins
for the room, etc). This will also help encapsulate things like "this is a best-of-x"
away from the code that it takes to run a single race.

### Encapsulate database access, and make "thread-safe"

Currently the bot accesses two databases, daily.db and races.db, which keep track of
the times for the speedrun daily and results of public races. Presumably more will be
added. It does this through sqlite3.

I would like to encapsulate all these accesses in a single class responsible for handling
the databases. One primary objective of doing this is to make these database accesses
"thread-safe" -- by this, I mean that because this program uses asyncio, it's possible
for two subroutines to be accessing the database at the same time, which may cause
problems with sqlite. We should add some sort of simple mutex to these accesses to
prevent this.