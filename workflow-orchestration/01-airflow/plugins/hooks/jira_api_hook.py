from airflow.hooks.base import BaseHook
import requests
from requests.auth import HTTPBasicAuth
import logging
from typing import List, Dict, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class JiraApiHook(BaseHook):
    """
    A custom Airflow hook for interacting with the Jira API.
    Handles authentication, pagination, and incremental syncing for issue searches.
    """
    
    def __init__(
        self,
        url: str,
        email: str,
        api_token: str,
        project_keys: List[str],
        conn_id: str = None,
        *args,
        **kwargs
    ):
        """
        Initialize the Jira API hook.
        
        :param url: Jira instance URL (e.g., https://your-jira-instance.atlassian.net)
        :param email: Jira user email for authentication
        :param api_token: Jira API token
        :param project_keys: List of Jira project keys to query
        :param conn_id: Optional Airflow connection ID for credentials (if not using email/token)
        """
        super().__init__(*args, **kwargs)
        self.url = url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.project_keys = project_keys
        self.conn_id = conn_id
        self.auth = None
        self.headers = {"Accept": "application/json"}
        
        if self.conn_id:
            conn = self.get_connection(self.conn_id)
            self.url = conn.host.rstrip("/")
            self.email = conn.login
            self.api_token = conn.password
            self.project_keys = conn.extra_dejson.get("project_keys", self.project_keys)
        
        if not all([self.url, self.email, self.api_token, self.project_keys]):
            raise ValueError("Missing required parameters: url, email, api_token, or project_keys")
        
        self.auth = HTTPBasicAuth(self.email, self.api_token)
    
    def fetch_issues(
        self,
        fields: List[str],
        last_sync_timestamp: str = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch issues from Jira API for specified project keys.
        
        :param fields: List of Jira API fields to retrieve (e.g., ['summary', 'status'])
        :param last_sync_timestamp: ISO timestamp for incremental sync (e.g., '2025-05-14T11:09:00+00:00')
        :param max_results: Number of issues per API request
        :return: List of issue records
        """
        all_records = []
        
        last_sync = None
        if last_sync_timestamp:
            try:
                last_sync = datetime.fromisoformat(last_sync_timestamp.replace("Z", "+00:00"))
                logger.info(f"Fetching issues updated since {last_sync}")
            except ValueError:
                logger.warning(f"Invalid last_sync_timestamp: {last_sync_timestamp}, performing full sync")
        
        for project_key in self.project_keys:
            start_at = 0
            while True:
                try:
                    time.sleep(1)  # Avoid rate limits
                    endpoint = f"{self.url}/rest/api/3/search"
                    jql = f"project = {project_key}"
                    if last_sync:
                        jql += f" AND updated >= '{last_sync.strftime('%Y-%m-%d %H:%M')}'"
                    query = {
                        "jql": jql,
                        "fields": ",".join(fields),
                        "maxResults": max_results,
                        "startAt": start_at
                    }
                    
                    response = requests.get(
                        endpoint,
                        headers=self.headers,
                        params=query,
                        auth=self.auth
                    )
                    
                    if response.status_code == 429:
                        logger.error(f"Rate limit exceeded for project {project_key}. Consider increasing delay or reducing max_results.")
                        raise Exception("Jira API rate limit exceeded")
                    elif response.status_code in (401, 403):
                        logger.error(f"Authentication failed for project {project_key}. Check email and api_token.")
                        raise Exception("Jira API authentication failed")
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    issues = data.get("issues", [])
                    if not issues:
                        break
                    
                    all_records.extend(issues)
                    start_at += max_results
                
                except requests.exceptions.RequestException as e:
                    logger.error(f"Failed to fetch issues for project {project_key}: {str(e)}")
                    raise Exception(f"Failed to fetch issues: {str(e)}")
        
        logger.info(f"Fetched {len(all_records)} total records from Jira")
        return all_records
    
    def test_connection(self) -> tuple[bool, str]:
        """
        Test the Jira API connection by making a simple request.
        
        :return: Tuple of (success, message)
        """
        try:
            response = requests.get(
                f"{self.url}/rest/api/3/myself",
                headers=self.headers,
                auth=self.auth
            )
            response.raise_for_status()
            return True, "Jira API connection successful"
        except requests.exceptions.RequestException as e:
            return False, f"Jira API connection failed: {str(e)}"