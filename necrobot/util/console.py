import logging


def info(info_str):
    print('{}'.format(info_str))
    logging.getLogger('discord').info(info_str)


def error(error_str):
    print('Error: {}'.format(error_str))
    logging.getLogger('discord').warning(error_str)
