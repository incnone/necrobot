import logging


def debug(info_str):
    # print(info_str)
    logging.getLogger('necrobot').debug(info_str)


def info(info_str):
    # print(info_str)
    logging.getLogger('necrobot').info(info_str)


def error(error_str):
    # print(error_str, file=sys.stderr)
    logging.getLogger('necrobot').warning(error_str)
