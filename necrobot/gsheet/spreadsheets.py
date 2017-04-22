"""
Tools for interacting with a GSheet, typically for a CoNDOR Event.
"""

import asyncio
import httplib2
import unittest

from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

from necrobot.util.config import Config


DISCOVERY_URL = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


_sheet_lock = asyncio.Lock()


class Spreadsheets(object):
    """
    Context manager; Returns a spreadsheets() majig 
    (https://developers.google.com/resources/api-libraries/documentation/sheets/v4/python/latest/
    sheets_v4.spreadsheets.html)
    """
    initted = False
    credentials = None
    sheet_service = None

    def __init__(self):
        if not Spreadsheets.initted:
            self._get_credentials()
            self._build_service()
            Spreadsheets.initted = True

    def __enter__(self):
        return Spreadsheets.sheet_service.spreadsheets()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def _get_credentials():
        if Spreadsheets.credentials is None:
            Spreadsheets.credentials = ServiceAccountCredentials.from_json_keyfile_name(
                filename=Config.OAUTH_CREDENTIALS_JSON,
                scopes=SCOPES
            )

    @staticmethod
    def _build_service():
        http = Spreadsheets.credentials.authorize(httplib2.Http())
        Spreadsheets.sheet_service = discovery.build(
            'sheets', 'v4', http=http, discoveryServiceUrl=DISCOVERY_URL)


def sheet_locked(func):
    """
    Decorator; obtains the _sheet_lock Lock before running the function
    """
    def func_wrapper(*args, **kwargs):
        with (yield from _sheet_lock):
            func(*args, **kwargs)
    return func_wrapper


class TestSpreadsheets(unittest.TestCase):
    def test_get(self):
        with Spreadsheets():
            pass
