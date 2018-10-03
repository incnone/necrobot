import necrobot.exception


class Keyword(object):
    def __init__(
            self,
            keyword: str,
            num_args: int = 0,
            param_for: str = None,
            aliases: list = list()
    ):
        self.keyword = keyword.lower()
        self.num_args = num_args
        self.param_for = param_for
        self.aliases = aliases

    def __hash__(self):
        return hash(self.keyword)
    
    def __eq__(self, other):
        return self.keyword == other.keyword

    @property
    def keyword_name(self):
        if self.param_for is not None:
            return self.param_for
        else:
            return self.keyword


def get_keyword(arg: str, keyword_set: set) -> Keyword or None:
    """Returns a Keyword object from keyword_set corresponding to the given string.
    
    Parameters
    ----------
    arg: str
        The argument to find a keyword for.
    keyword_set: set
        The set of Keywords to search.

    Returns
    -------
    Optional[Keyword]
        The found Keyword, or None if none found.
    """
    arg = arg.lower().lstrip('-')
    for keyword in keyword_set:
        if arg == keyword.keyword or arg in keyword.aliases:
            return keyword

    return None


def parse(args: list, keyword_set: set) -> dict:
    """Parses a list of strings into a dictionary whose keys are the keys in keyword_dict, and such that the value
    at the key K is a list of the next keyword_dict[K] strings after K in the list args.
    
    All keys in keyword_dict should be lowercase; keywords are not parsed case-sensitively. The returned dict holds
    a list of args that were not successfully parsed under the empty-string key.
    
    Parameters
    ----------
    args: list[str]
        A list of strings, meant to represent a shlex-split user-input.
    keyword_set: set[Keyword]
        A dict whose keys are keywords, and whose values are the number of parameters following the keyword to 
        parse out.
        
    Returns
    -------
    dict[str: list[str]]
        The parsed dictionary, mapping Keyword.keyword to their list of parameters.
    """
    parsed_dict = {'': []}
    while args:
        keyword = get_keyword(arg=args[0], keyword_set=keyword_set)

        if keyword is not None:
            args.pop(0)
            keyword_name = keyword.keyword_name

            if keyword_name in parsed_dict:
                raise necrobot.exception.DoubledArgException(keyword=keyword.keyword)

            if keyword.param_for is not None:
                parsed_dict[keyword_name] = [keyword.keyword]
            else:
                parsed_dict[keyword_name] = []
                num_args_pulled = 0
                while num_args_pulled < keyword.num_args:
                    if not args:
                        raise necrobot.exception.NumParametersException(
                            keyword=keyword,
                            num_expected=keyword.num_args,
                            num_given=num_args_pulled
                        )
                    else:
                        num_args_pulled += 1
                        parsed_dict[keyword_name].append(args[0])
                        args.pop(0)
        else:
            parsed_dict[''].append(args[0])
            args.pop(0)

    return parsed_dict
