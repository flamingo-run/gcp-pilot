import unittest
from unittest.mock import patch

from gcp_pilot.sheets import Spreadsheet  # pylint: disable=unused-import
from tests import ClientTestMixin


class TestSheets(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = Spreadsheet

    def get_client(self, **kwargs):
        with patch("gspread.Spreadsheet.fetch_sheet_metadata", return_value={"properties": {}}):
            return super().get_client(sheet_id="chuck_norris")
