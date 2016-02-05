# Necrobot documentation (v 0.4)

In general, the bot will respond to commands in the main bot channel (#necrobot_main), or via PM. (Race-specific commands should be entered in the race room.)

## Common Commands

In general, `.help` will give you a list of all the commands available in a given channel. `.help <command>` (with `<command>` replaced by the name of a command) will give you more information about that particular command. Here are some of the more common commands you'll use, with examples:

### For the daily speedruns

There are currently two daily speedruns; one for Cadence, and one which rotates between the other 9 characters. You can find out the current character with `.dailychar`, or get the upcoming schedule with `.dailyschedule`. If you want to know when a character will next appear, try for example `.dailywhen coda`. Calling `.dailywhen` alone will tell you how long until the next daily opens (new dailies open at 0 UTC).

To get the seed for today's daily, call `.dailyseed` (either in the main channel or via PM). Make your run, then submit your result with `.dailysubmit 12:34.56`, or, if you died, `.dailysubmit death 3-2`. (Use 4-4 for Dead Ringer and 4-5 for the Necrodancer.) The `.dailysubmit` command should be called in PM or in the spoilerchat channel.

For the rotating-character daily, just add `rot` to all these commands: Call `.dailyseed rot` to get the seed for the rotating-character daily, and `.dailysubmit rot 12:34.56` to submit a time. (You can also call `.dailysubmit 12:34.56` in the rotating-character spoilerchat.)

### For races

To make a seeded Cadence race, call `.make` in #necrobot_main. Unseeded races are made with `.make u`. You can specifiy a character: `.make Dorian`; or a seed: `.make -s 12345`; or a custom description: `.make -custom "4-shrine"`. These flags can be combined: `.make Bolt u -custom "Nuzlocke"`.

To enter a race, go to the race room (it's a text channel called something like `#cadence_s7`, for a Cadence seeded race), and call `.enter`. If the race is already in progress, you'll have to wait for the next one; call `.notify` in the race room to have the bot send an @mention at you when a rematch is made. 

After entering, call `.ready` to indicate your readiness to begin the race. The race will start when every entrant is ready. When you successfully step on the end stairs, call `.done` and the bot will record your time. You can also ask the bot to record an in-game-time for your run with `.igt 12:34.56`.

If you wish to forfeit the race call `.forfeit`. The bot will record the time of your forfeit. You can specify a level of death with `.death 3-2`. Whether you win or forfeit, you can add a comment to your run with `.comment <whatever>`. 

Most of the commands can be taken back if you make them in error: Use `.unenter`, `.unready`, `.undone`, and `.unforfeit`.

After the race is over, call `.rematch` to make a new race room with the same rules. This will @mention anyone who called `.notify` as well as all the entrants to the previous race; you can elect to not be notified for a rematch with `.notify off`. 

### User preferences

You can choose to receive alerts when races happen, or to be automatically PM'd the seeds for a new daily, or to automatically hide the spoilerchat when you haven't submitted for a daily. These are all modified with the `.setprefs` command; call `.help setprefs` for complete information. You can see your current preferences with `.viewprefs`.

## Command list

### Seed generation

- `.randomseed [n]` : Generate n random seeds, which will be sent via PM. If n is not specified, the bot will generate one seed and send it in the channel in which this command was called. Currently n is limited to 20.

### User preferences

- `.setprefs [-spoilerchat show|hide] [-dailyalert none|all|cadence|rotating] [-racealert none|some|all]` : Sets user preferences. 
    - `spoilerchat` : `show` makes spoilerchat visible at all times; `hide` hides it from you until after you've submitted for the appropriate daily.
    - `dailyalert` : `cadence` or `rotating` will PM the seed for that daily to you when that daily opens. `all` will do both.
    - `racealert` : `some` sends a PM when a new race is created, but not when a rematch is created. `all` sends a PM in both cases.

- `.viewprefs` (alias `.getprefs`) : Send a summary of your user prefs via PM.

### Daily

In general, the `-rot` flag, where applicable, calls the command for the rotating-character daily; omitting this flag calls it for the Cadence daily.

- `.dailychar` (alias `.dailywho`) : Get the current character for the rotating-character daily.
- `.dailyinfo [-rot] [character]` (alias `.dailywhen`) : Get the time until the next daily opens. If a character is specified, this will instead tell you when that character is next featured on the rotating-character daily.
- `.dailyresubmit [-rot] [12:34.56|death x-y]` : Submit for the daily, overriding a previous submission. Arguments are the same as for `.dailysubmit`.
- `.dailyrules [-rot]` : Get the rules for the daily.
- `.dailyschedule` : Get a list of the upcoming characters for the rotating-character daily.
- `.dailyseed [-rot]` : Get the seed for the current daily. "Current" means the current date in UTC. 
- `.dailystatus [-rot]` : Get your status for the daily, i.e., whether you are registered (have called `.dailyseed`) and whether you've submitted.
- `.dailysubmit [-rot] [12:34.56|death [x-y]]` : Submit for the daily. `12:34.56` is an in-game time and indicates finishing the run in that time; `death x-y` indicates a death on the appropriate level. This will give an error if you've already submitted; use `.dailyresubmit` to correct a prior submission, or `.dailyunsubmit` to remove one. This command attempts to submit for the daily for which you've most recently called `.dailyseed`. Submissions for a daily are accepted until 01:00 UTC the next day -- that is, you have a one-hour grace period after the daily closes to get submissions in.
- `.dailyunsubmit [-rot]` : Remove your most recent daily submission. This only works if that daily is still open.

### Races

#### Making races

- `.make [char] [u|s|-seed 12345] [-custom "some description"]` : Makes a new public race. `char` gives the character for the race (must be a Necrodancer character). `u` makes an unseeded race; `s` makes a seeded race (default); `-seed 12345` makes a race with the specified particular seed. (The seed must be an integer; text seeds are not supported.) `-custom "4-shrine"` makes a race with the given description attached to it.

- `.makeprivate [-a admin...] [-r racer...] [-c char] [-u|-s|-seed 12345] [-custom "some description]` : Make a new private race. `admin...` is a list of race admins, who can both see the room and can use some admin-specific commands, and `racer...` is a list of racers, who can see the room. The other commands are the same as for `.make`.

#### Racer commands

- `.enter` (alias `.join`): Enter the race.
- `.unenter` (alias `.unjoin`): Leave the race (undoes a previous `.enter`.)
- `.ready` : Indicate you are ready to begin the race. The race begins when all racers are ready.
- `.unready` : Undoes a previous `.ready`.
- `.done` (alias `.finish`): Finish the race successfully. The bot will record your time.
- `.undone` (alias `.unfinish`): Undoes a previous `.done`.
- `.forfeit [comment]` (alias `.quit [comment]`): Forfeits the race. The bot will record the time of forfeit; `comment` adds the given text as a comment to your race.
- `.unforfeit` (alias `.unquit`): Undoes a previous `.forfeit`.
- `.comment [text]`: Adds the given text as a comment to your race.
- `.death x-y`: Forfeits the race if you are not already forfeit, and records `x-y` as the level of death.
- `.igt 12:34.56`: Records the given time as an in-game time for your race.
- `.rematch`: If the race is complete, makes a rematch.
- `.delayrecord`: Delays recording of the race for an extra 120 seconds, if the race is not already being delayed.
- `.notify [off]`: Will send an @mention to you when a rematch for this race is created. Such mentions are automatically sent to racers. You can disable this mention with `.notify off`.
- `.time`: Get the current race time.
- `.missing`: List users that were @notified but who have not yet entered the race.
- `.poke`: Give an @mention poke to users that have entered but are not ready, if either only one or fewer than 1/4 are unready.
- `.admins`: In a private race, lists the admins for the given race.

#### Admin commands

- `.forcecancel`: Cancels the race; no results will be recorded.
- `.forceclose`: Cancels the race and closes the race room.
- `.forceforfeit [racer...]`: Forces the specified racers to forfeit, even if they've already finished.
- `.forceforfeitall`: Forces any unfinished racers to forfeit.
- `.kick [racer...]`: Unenters the specified racers from the race. (They can re-enter with `.enter`; this command is intended for kicking idle/afk users rather than channel moderation.)

- `.ready`: Indicates that admins are ready to begin the race. (If caller is also a racer, also readies that racer for the race.) This must be called just once by any admin before the race can begin, if there are any admins.
- `.unready`: Indicates that admins are no longer ready to begin the race.
- `.add [username...]`: Gives permission to see the room to the specified users.
- `.remove [username...]`: Removes permission to see the room from the specified users.
- `.changerules [char] [u|s|-seed 12345] [-custom "some description"]`: Changes the rules for the race. Parameters are the same as `.make`.
- `.makeadmin [username...]`: Makes the specified users admins for the race. (This cannot be undone.)
- `.reseed`: If the race is seeded (and the seed was not specified), generates a new random seed. (To specify a particular seed, use `.changerules -seed 12345`.)
- `.forcereset`: Cancel and reset the current race.
- `.pause`: Pause the race timer.
- `.unpause`: Unpause the race timer.


