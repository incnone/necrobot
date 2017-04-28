"""
A match is a collection of races between exactly two racers. These races share a common private channel, visible to
admins and to the racers, which is used only for this match.

`Match` is the main data class, and represents a row of the database table `matches`. Because `Match`es interact with
the databse very closely, they should never be created through their constructor. The appropriate factory method is
`matchutil.make_match`. 

A `Match` contains: uIDs for both racers; a MatchInfo; scheduling information; and some other match-related information.

A `MatchInfo` contains a `RaceInfo` (the default race type) as well as the number of races (and whether the match is
a best-of). 

`matchutil` is the factory class, and also contains useful methods for finding collections of matches via the database.
It could probably benefit from a refactor.

`MatchRoom` is the BotChannel associated with running a match.

`MatchRaceData` is a convenience class (more of a struct) for storing data about the set of races in a match. It
roughly corresponds to a row of the database table `match_races`.
"""