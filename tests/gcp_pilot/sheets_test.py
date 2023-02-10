import unittest
from unittest.mock import Mock, patch

from gcp_pilot.mocker import patch_auth
from gcp_pilot.sheets import Spreadsheet
from tests import ClientTestMixin


class TestSheets(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = Spreadsheet

    def get_client(self, **kwargs):
        with patch("gspread.Spreadsheet.fetch_sheet_metadata", return_value={"properties": {}}):
            return super().get_client(sheet_id="chuck_norris")

    @patch_auth()
    def test_init_sheet_id(self):
        sheet_id = "1x36dOSowEOopieX0rvMewWEzhd29z2lMLtn38xhWZJU"
        sheet_url = "https://docs.google.com/spreadsheets/d/1x36dOSowEOopieX0rvMewWEzhd29z2lMLtn38xhWZJU/edit"

        gclient = Mock(spec=["open_by_key"])
        with patch("gspread.Client", return_value=gclient):
            spreadsheet = self._CLIENT_KLASS(sheet_id)

        self.assertEqual(sheet_id, spreadsheet.sheet_id)
        self.assertEqual(sheet_url, spreadsheet.url)
        gclient.open_by_key.assert_called_once_with(sheet_id)

    @patch_auth()
    def test_init_sheet_url(self):
        sheet_id = "1x36dOSowEOopieX0rvMewWEzhd29z2lMLtn38xhWZJU"
        sheet_url = "https://docs.google.com/spreadsheets/d/1x36dOSowEOopieX0rvMewWEzhd29z2lMLtn38xhWZJU/edit"

        gclient = Mock(spec=["open_by_key"])
        with patch("gspread.Client", return_value=gclient):
            spreadsheet = self._CLIENT_KLASS(sheet_url)

        self.assertEqual(sheet_id, spreadsheet.sheet_id)
        self.assertEqual(sheet_url, spreadsheet.url)
        gclient.open_by_key.assert_called_once_with(sheet_id)
