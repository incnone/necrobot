"""
A "league" is a collection of matches and/or races. It has its own separate schema on the MySQL server, and is uniquely
identified by the name of that schema. The primary purpose of a league is to represent a CoNDOR event, but it is also
used for the Necrobot ladder.

`League` is the main data class; it contains information about the types of matches run in the league, as well as
information about how the bot should behave in this particular league. Leagues can have very unusual rules, so no
effort is made to encode all the information about a league's ruleset into the database. Instead, we store some
simple information -- a default race and match type -- and a separate unique identifier, which this bot can use to
determine custom code to run for the league.

Thus "custom code" is useful in determining how the league should make automatches and other administrative things,
as well as being able to define custom match types (e.g. rotating characters) that are too complicated, relative to
how common they are, to store in the database.
"""