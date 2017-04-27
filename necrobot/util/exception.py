class NecroException(Exception):
    pass


class NoMatchupExistsException(NecroException):
    pass


class DuplicateUserException(NecroException):
    def __init__(self, err_str):
        self._err_str = err_str

    def __str__(self):
        return self._err_str


class NotFoundException(NecroException):
    pass


class TimeoutException(NecroException):
    pass


# DatabaseException -------------------------------------

class DatabaseException(NecroException):
    pass


class LeagueAlreadyExists(DatabaseException):
    def __init__(self, exc_str=None):
        self._exc_str = exc_str

    def __str__(self):
        return self._exc_str if self._exc_str is not None else ''


class LeagueDoesNotExist(DatabaseException):
    pass


class InvalidSchemaName(DatabaseException):
    pass


# ParseException ------------------------------------------------------
class ParseException(NecroException):
    def __init__(self, err_str):
        self._err_str = err_str

    def __str__(self):
        return self._err_str


class DoubledArgException(ParseException):
    def __init__(self, keyword):
        self.keyword = keyword

    def __str__(self):
        return 'Doubled argument ({0}).'.format(self.keyword)


class NumParametersException(ParseException):
    def __init__(self, keyword: str, num_expected: int, num_given: int):
        self.keyword = keyword
        self.num_expected = num_expected
        self.num_given = num_given

    def __str__(self):
        return 'Incorrect number of parameters for argument {0} ({1} expected, {2} given).'.format(
            self.keyword,
            self.num_expected,
            self.num_given
        )
