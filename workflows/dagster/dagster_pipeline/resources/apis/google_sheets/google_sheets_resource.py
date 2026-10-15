# dagster_pipeline/resources/apis/google_sheets_resource.py
"""Google Sheets access via a service account (gspread)."""

import gspread
from gspread.http_client import BackOffHTTPClient
from dagster import ConfigurableResource
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class GoogleSheetsResource(ConfigurableResource):
    """Service-account credentials for Google Sheets.

    The service account must be shared (Editor) on every spreadsheet it writes to.
    `private_key` is the PEM key from the service account's JSON key file; literal
    "\\n" sequences (as stored in .env) are converted to newlines.
    """

    client_email: str
    client_id: str
    private_key_id: str
    private_key: str

    def get_client(self) -> gspread.Client:
        info = {
            "type": "service_account",
            "client_email": self.client_email,
            "client_id": self.client_id,
            "private_key_id": self.private_key_id,
            "private_key": self.private_key.replace("\\n", "\n"),
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        # BackOffHTTPClient retries rate-limited (429) / transient API errors with exponential backoff.
        return gspread.authorize(
            Credentials.from_service_account_info(info, scopes=SCOPES), http_client=BackOffHTTPClient
        )
