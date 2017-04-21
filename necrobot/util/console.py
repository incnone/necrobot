import logging
import sys


def info(info_str):
    print('{}'.format(info_str))
    logging.getLogger('discord').info(info_str)


def error(error_str):
    print('{}'.format(error_str), file=sys.stderr)
    logging.getLogger('discord').warning(error_str)
