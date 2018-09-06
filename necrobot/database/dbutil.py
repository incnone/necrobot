league_schema_name = None


def tn(tablename: str) -> str:
    if league_schema_name is not None:
        return '`{0}`.`{1}`'.format(league_schema_name, tablename)
    else:
        return '`{0}`'.format(tablename)
