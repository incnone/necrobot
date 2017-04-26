from necrobot.league.leaguemgr import LeagueMgr


def tn(tablename: str) -> str:
    league = LeagueMgr().league
    if league is not None:
        return '`{0}`.`{1}`'.format(league.schema_name, tablename)
    else:
        return '`{0}`'.format(tablename)