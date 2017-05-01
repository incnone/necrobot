import inspect
import logging
import sys
import traceback
import typing


def debug(info_str: str):
    caller_mod_name = inspect.getmodule(inspect.stack()[1][0]).__name__
    logging.getLogger('necrobot').debug('[{0}] {1}'.format(caller_mod_name, info_str))


def info(info_str: str):
    caller_mod_name = inspect.getmodule(inspect.stack()[1][0]).__name__
    logging.getLogger('necrobot').info('[{0}] {1}'.format(caller_mod_name, info_str))


def warning(error_str: str):
    caller_mod_name = inspect.getmodule(inspect.stack()[1][0]).__name__
    logging.getLogger('necrobot').warning('[{0}] {1}'.format(caller_mod_name, error_str))


def error(error_str: str):
    caller_mod_name = inspect.getmodule(inspect.stack()[1][0]).__name__
    logging.getLogger('necrobot').error('[{0}] {1}'.format(caller_mod_name, error_str), exc_info=True)


def critical(error_str: str):
    caller_mod_name = inspect.getmodule(inspect.stack()[1][0]).__name__
    logging.getLogger('necrobot').critical('[{0}] {1}'.format(caller_mod_name, error_str), exc_info=True)
