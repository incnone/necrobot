"""
Tools for interacting with a GSheet, typically for a CoNDOR Event.
"""

import asyncio
import httplib2
import unittest

from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

from necrobot.config import Config


DISCOVERY_URL = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


class Spreadsheets(object):
    """
    Context manager; Returns a spreadsheets() majig 
    (https://developers.google.com/resources/api-libraries/documentation/sheets/v4/python/latest/
    sheets_v4.spreadsheets.html)
    """
    initted = False
    credentials = None
    sheet_service = None
    _sheet_lock = asyncio.Lock()

    def __init__(self):
        if not Spreadsheets.initted:
            self._get_credentials()
            self._build_service()
            Spreadsheets.initted = True

    async def __aenter__(self):
        await Spreadsheets._sheet_lock.acquire()
        return Spreadsheets.sheet_service.spreadsheets()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        Spreadsheets._sheet_lock.release()

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


class TestSpreadsheets(unittest.TestCase):
    from necrobot.test.asynctest import async_test
    loop = asyncio.new_event_loop()

    @async_test(loop)
    async def test_get(self):
        async with Spreadsheets():
            pass
