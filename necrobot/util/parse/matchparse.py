import unittest
import necrobot.exception

from necrobot.util.parse import parseutil
from necrobot.util.parse.parseutil import Keyword
from necrobot.util.character import NDChar


matchtype_keywords = {
    # Match info
    Keyword(keyword='bestof', num_args=1),
    Keyword(keyword='repeat', num_args=1),
    Keyword(keyword='ranked'),
    Keyword(keyword='unranked'),

    # Race info
    Keyword(keyword='seeded', aliases=['s']),
    Keyword(keyword='unseeded', aliases=['u']),
    Keyword(keyword='seed', num_args=1),
    Keyword(keyword='dlc', aliases=['amplified']),
    Keyword(keyword='nodlc', aliases=['classic']),
    Keyword(keyword='character', num_args=1),

    # Race recording
    Keyword(keyword='nopost'),
    Keyword(keyword='post'),

    # Custom descriptor
    Keyword(keyword='custom', num_args=1),
}


for char in NDChar:
    matchtype_keywords.add(Keyword(keyword=str(char), param_for='character'))


def parse_matchtype_args(args: list) -> dict:
    """Parses a list of strings into a dictionary whose keys are the keys in matchtype_keywords, and such that the 
    value at the key K is a list of the next matchtype_keywords[K] strings after K in the list args.

    Parameters
    ----------
    args: list[str]
        A list of strings, meant to represent a shlex-split user-input.

    Returns
    -------
    dict[str: list[str]]
        The parsed dictionary.
    """

    parsed_dict = parseutil.parse(args=args, keyword_set=matchtype_keywords)
    if 'bestof' in parsed_dict and int(parsed_dict['bestof'][0]) % 2 == 0:
        raise necrobot.exception.ParseException(
            "Can't make a best-of-{0} match because {0} is even.".format(parsed_dict['bestof'])
        )
    return parsed_dict


class TestMatchParse(unittest.TestCase):
    def test_parse(self):
        import shlex
        from necrobot.exception import DoubledArgException, NumParametersException

        parse_string_fail_num = 'cadence bestof'
        parse_string_fail_dup = 'cadence diamond s'
        parse_string_success = 'cadence s bestof 3 ranked custom "Custom description"'
        parsed_dict = {
            'character': ['cadence'],
            'seeded': [],
            'bestof': ['3'],
            'ranked': [],
            'custom': ['Custom description'],
            '': []
        }
        parsed_args = parse_matchtype_args(shlex.split(parse_string_success))

        self.assertEqual(parsed_args, parsed_dict)
        self.assertRaises(parse_matchtype_args, DoubledArgException, parse_string_fail_dup)
        self.assertRaises(parse_matchtype_args, NumParametersException, parse_string_fail_num)
