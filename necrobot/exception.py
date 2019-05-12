class NecroException(Exception):
    def __init__(self, err_str: str = None):
        self._err_str = err_str

    def __str__(self):
        if self._err_str is None:
            return type(self)
        else:
            return '{type}: {what}'.format(type=type(self).__name__, what=self._err_str)


class NoMatchupExistsException(NecroException):
    pass


class DuplicateUserException(NecroException):
    pass


class BadInputException(NecroException):
    pass


class NotFoundException(NecroException):
    pass


class TimeoutException(NecroException):
    pass


class AlreadyInitializedExecption(NecroException):
    pass


class IncorrectWksException(NecroException):
    pass


class DuplicateMatchException(NecroException):
    pass


# DatabaseException -------------------------------------

class DatabaseException(NecroException):
    pass


class LeagueAlreadyExists(DatabaseException):
    pass


class LeagueDoesNotExist(DatabaseException):
    pass


class InvalidSchemaName(DatabaseException):
    pass


# ParseException ------------------------------------------------------
class ParseException(NecroException):
    pass


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
