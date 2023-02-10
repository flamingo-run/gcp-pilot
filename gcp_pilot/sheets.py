import gspread
from google.auth.transport.requests import AuthorizedSession
from gspread.client import extract_id_from_url

from gcp_pilot.base import GoogleCloudPilotAPI


class Spreadsheet(GoogleCloudPilotAPI):
    _scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    def __init__(self, sheet_id: str, **kwargs):
        super().__init__(**kwargs)
        if sheet_id.startswith("https://"):
            sheet_id = extract_id_from_url(sheet_id)
        self.sheet_id = sheet_id
        self.spreadsheet = self.client.open_by_key(self.sheet_id)

    def worksheet(self, name: str) -> gspread.Worksheet:
        return self.spreadsheet.worksheet(name)

    @classmethod
    def _client_class(cls, credentials, **kwargs):
        client = gspread.Client(auth=credentials)
        client.session = AuthorizedSession(credentials)
        return client

    @property
    def url(self) -> str:
        return f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit"


__all__ = ("Spreadsheet",)
