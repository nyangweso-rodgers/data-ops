from airflow.hooks.base import BaseHook
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from typing import Dict, List, Any, Optional
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

class CCSApiHook(BaseHook):
    """
    A custom hook to interact with the CCS API.
    Handles token generation with 1-hour expiration and fetching records from any endpoint.
    """
    TOKEN_URL = "https://api.callcenterstudio.com/application/access_token/"

    def __init__(self, ccs_conn_id: str, endpoint: str):
        super().__init__()
        self.ccs_conn_id = ccs_conn_id
        self.endpoint = endpoint
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        load_dotenv()

    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Generate headers for API requests, refreshing token if expired."""
        if not self.access_token or (self.token_expires_at and datetime.utcnow() >= self.token_expires_at):
            self.generate_token()
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Tenant": os.getenv("CCS_TENANT"),
        }
        if include_auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def generate_token(self) -> None:
        """Generate or refresh an access token with 1-hour expiration."""
        headers = self._get_headers(include_auth=False)
        payload = {
            "client_id": os.getenv("CCS_CLIENT_ID"),
            "client_secret": os.getenv("CCS_CLIENT_SECRET"),
        }
        try:
            response = requests.post(self.TOKEN_URL, headers=headers, json=payload)
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            self.token_expires_at = datetime.utcnow() + timedelta(hours=1)
            logger.info("New access token generated with 1-hour expiration.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating access token: {e}")
            raise

    def fetch_records(
        self,
        start_date: str,
        finish_date: str,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Fetch raw records from the specified endpoint with pagination.
        Returns raw data for destination-specific transformation.
        Args:
            start_date (str): Start date in 'YYYY-MM-DD HH:MM:SS' format.
            finish_date (str): Finish date in 'YYYY-MM-DD HH:MM:SS' format.
            limit (int): Number of records per request.
            cursor (Optional[str]): Pagination cursor.
        Returns:
            Tuple of (records, cursor) where records are raw API data.
        """
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retries))

        headers = self._get_headers()
        params = {
            "start_date": start_date,
            "finish_date": finish_date,
            "limit": limit,
        }
        if cursor:
            params["cursor"] = cursor

        logger.info(f"Fetching from {self.endpoint} with params: {params}")

        try:
            response = session.get(self.endpoint, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            call_data = data.get("call_details_list", [])
            cursor = data.get("cursor")

            if not call_data:
                logger.info("No more records to fetch.")
            return call_data, cursor
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching records from {self.endpoint}: {e}")
            if isinstance(e, requests.exceptions.ConnectionError):
                logger.info("Connection error detected, attempting to refresh token.")
                self.generate_token()
                headers["Authorization"] = f"Bearer {self.access_token}"
                try:
                    response = session.get(self.endpoint, headers=headers, params=params, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                    call_data = data.get("call_details_list", [])
                    cursor = data.get("cursor")
                    return call_data, cursor
                except requests.exceptions.RequestException as e:
                    logger.error(f"Retry failed after refreshing token: {e}")
                    raise
            raise