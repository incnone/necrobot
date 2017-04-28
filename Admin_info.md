# Condorbot admin info (v 0.10)

Condorbot and Necrobot now run on the same codebase, but their configurations are different. Therefore, to 
restart or kill Condorbot, go into the `necrobot` folder on the server and call `./start-condorbot.sh` or
`./kill-condorbot.sh`.

The old version of Condorbot is still available, and a version is stored in the `condorbot` folder on the
server. You can get that version by calling the appropriate scripts inside that folder. (Remember to kill
the newer version first in that case, or you will see the bot reacting twice to most commands.)

There's a new admin command available in all channels, but undocumented in `.help`, called `.force`. This
can simulate a user entering a specific command from the bot's point of view. For instance, you could set
my twitch stream to `djc6986` by calling `.force incnone .twitch djc6986`.

User data is now persistent between events, so many people will not need to re-register when new events
happen.

## Event setup

Condorbot can manage a single CoNDOR event at a time. Each such event has its own schema on the MySQL server.

### Create a new event

To create an event, call `.register-condor-event` in #adminchat. Supply this command with the name of the
schema you wish to create for the event; this should be short and unique (e.g. `condor_s5`, `ndwc`, 
`diamondor`). 

This will also set the bot's default event to the newly created event, which tells the bot to record matches
in that schema. You can change the bot's default event with `.setevent` (though I can't imagine any case where
you would want to).

### Change the event's default match rules

Give the event a more descriptive name with `.setname`, such as `.setname CoNDOR Season 5`. 

More importantly, set the default match rules for the event with `.setrules`; this lets you specify the 
default type of match. For instance, DiamonDOR matches could be made with `.setrules diamond s repeat 3`. 
(By default, the rules are Cadence seeded, repeat-3.) You can see the current rules with `.rules`.

Previous seasons have often had a weekly deadline that matches need to be scheduled before. You can set
such a deadline using `.setdeadline`, e.g., `.setdeadline friday 12a` forces matches to be scheduled before
friday UTC (the Season 5 deadline).

### Set up the GSheet

I recommend having a "backend" GSheet that Condorbot interacts with. 

#### Point the bot to the GSheet

Every GSheet has a URL that looks like docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={worksheet_id}. The
sheet ID is a long string of letters and numbers; it uniquely identifies the spreadsheet. Tell the bot you want
to be working with a spreadsheet by calling `.setgsheet sheet_id`. 

The bot needs read and write permissions for the sheet, and will complain if it does not have them. Give edit
permission to `necrobot@incnone-necrobot.iam.gserviceaccount.com` before calling `.setgsheet`.

You can check that you're pointing at the right GSheet by calling `.gsheet`, which will return a link to your
sheet as well as its title.

#### Structure of a match worksheet

For any worksheet you wish to make matches from, the bot expects the following columns:

- `Racer 1`, `Racer 2`, `Date`, `Cawmentary`, `Winner`, `Score`, `RTMP`, `Vod`, `Match ID`

(The names of the columns do not need to be exactly the above, but they must contain those as substrings. For 
instance, `Date:` is a fine column name, as is `Game Score:`. The column orders are not important. Let me know 
if you want to change any of the above, which is easy but can't be done through the bot directly. `Match ID` 
is a column to be used by the bot alone, as a unique identifier for the match.)

#### Making matches from a worksheet

To make match rooms, create a worksheet structured as above, and fill the `Racer 1` and `Racer 2` columns
with the RTMP names of the racers in each match. Then call `.makematches worksheet_name` (e.g., for S5 
matches you might call `.makematches "Week 1"`). As before, this command is quite slow.

If you wish to add more matches, simply append those matches to the end of your sheet and call `.makematches`
again. Duplicate pairings of racers are allowed (though I am still working through some UI issues of how to
allow people to refer to them nicely, for instance for `.cawmentate` commands).

Note: Condorbot now behaves differently if it finds a name that isn't registered as an RTMP name: It checks 
that name against the Discord and Twitch names of all users in the Necrobot database (which is everyone who
has ever joined the Necrobot server, about 900 people), and assumes you mean any user it matches. I believe
this will be helpful but may lead to unintuitive bugs, TBD.

### Other commands/changes for #adminchat

There is no longer a `.closeweek`, but `.closeall` simply closes all match rooms, and `.closefinished` will
close only those whose matches are finished. `.dropracer` will close all of a particular racer's channels, and
also delete their matches from the database.

You can hand-make individual matches with `.makematch`, but these won't get registered with the GSheet in any
way, so the bot won't be able to post scheduling information etc. for them.

`.f-rtmp` is the old `.rtmp` command to change a user's RTMP. It should be much less buggy. Users can set their
own RTMP with `.rtmp`.

## Match rooms

Much of match room operation should be the same. I've renamed many admin commands and deleted some, to attempt
to get rid of a lot of the bloat and confusion with what command to call to achieve what effect.

The most useful commands are probably `.f-begin`, which is the old `.forcebeginmatch` and `.postpone`, which
unschedules a match.

For messing with individual races, `.changewinner` can change the winner of a race, and `.recordrace` can
manually record a race that didn't get caught by the bot (for instance, if the bot broke during a race).
