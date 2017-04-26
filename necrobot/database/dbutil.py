import necrobot.league.the_league


def tn(tablename: str) -> str:
    league = necrobot.league.the_league.league
    if league is not None:
        return '`{0}`.`{1}`'.format(league.schema_name, tablename)
    else:
        return '`{0}`'.format(tablename)
