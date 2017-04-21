import logging
import sys


def info(info_str):
    print(info_str)
    logging.getLogger('discord').info(info_str)


def error(error_str):
    print(error_str, file=sys.stderr)
    logging.getLogger('discord').warning(error_str)
