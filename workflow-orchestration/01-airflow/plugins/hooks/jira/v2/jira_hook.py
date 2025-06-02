import logging
from typing import Dict, List
from requests.exceptions import HTTPError
from airflow.models import Variable
from requests import Session
from datetime import datetime

logger = logging.getLogger(__name__)

class JiraApiHook:
    def __init__(self, log_level: str = 'INFO'):
        self._base_url = Variable.get('jira_url')
        self._session = None
        self.log_level = log_level

    def _init_session(self):
        if not self._session:
            self._session = Session()
            self._session.auth = (
                Variable.get('jira_email'),
                Variable.get('jira_api_token')
            )
            self._session.headers.update({'Accept': 'application/json'})
        return self._session

    def close(self):
        if self._session:
            self._session.close()
            self._session = None
            logger.info("Jira API session closed")

    def test_connection(self):
        try:
            session = self._init_session()
            response = session.get(f"{self._base_url}/rest/api/3/myself")
            response.raise_for_status()
            return True, "Connection successful"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def get_boards(self, project_keys: List[str]) -> List[Dict]:
        """
        Fetch all boards for given project keys.
        
        Args:
            project_keys: List of Jira project keys.
        
        Returns:
            List of board metadata dictionaries.
        """
        boards = []
        session = self._init_session()
        base_url = self._base_url.rstrip('/')  # Remove trailing slash
        for project_key in project_keys:
            start_at = 0
            while True:
                try:
                    response = session.get(
                        f"{base_url}/rest/agile/1.0/board",
                        params={
                            "projectKeyOrId": project_key.strip(),  # Ensure no leading/trailing spaces
                            "startAt": start_at,
                            "maxResults": 50
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    boards.extend(data["values"])
                    logger.info(f"Fetched {len(data['values'])} boards for project {project_key}, startAt={start_at}")
                    if data.get("isLast", True):
                        break
                    start_at += data.get("maxResults", 50)
                except HTTPError as e:
                    logger.warning(f"Error fetching boards for project {project_key}: {str(e)}")
                    # Log the response for debugging
                    if e.response:
                        logger.error(f"Response content: {e.response.text}")
                    break
        return boards

    def _map_sprint(self, sprint: Dict, mappings: List[Dict]) -> Dict:
        """
        Map sprint data to schema fields.
        
        Args:
            sprint: Raw sprint data from Jira API.
            mappings: Schema mappings from sprints.yml.
        
        Returns:
            Mapped sprint record.
        """
        record = {}
        for mapping in mappings:
            if mapping.get('auto_generated', False):
                continue
            target_field = mapping['target']
            source_path = mapping.get('source', target_field)
            value = sprint.get(source_path)
            record[target_field] = value
        return record

    def fetch_sprints(self, schema: Dict, board_id: int, state: str = 'active,closed,future', last_sync_timestamp: str = None, batch_size: int = 50):
        """
        Fetch sprints from a specific board, filtering by created_date and complete_date.
        
        Args:
            schema: Configuration with mappings.
            board_id: ID of the board.
            state: Sprint states to fetch.
            last_sync_timestamp: Last sync time for incremental fetch.
            batch_size: Number of sprints per batch.
        
        Yields:
            Batches of sprint records.
        """
        session = self._init_session()
        start_at = 0
        while True:
            try:
                response = session.get(
                    f"{self._base_url}/rest/agile/1.0/board/{board_id}/sprint",
                    params={"state": state, "maxResults": batch_size, "startAt": start_at}
                )
                response.raise_for_status()
                data = response.json()
                sprints = data.get('values', [])
                
                if not sprints:
                    break
                
                batch = []
                for sprint in sprints:
                    if not isinstance(sprint, dict) or 'id' not in sprint:
                        logger.warning(f"Skipping invalid sprint from board {board_id}: {sprint}")
                        continue
                    record = self._map_sprint(sprint, schema['mappings'])
                    if not record.get('id'):
                        logger.warning(f"Skipping sprint with missing id from board {board_id}: {record}")
                        continue
                    # Filter based on created_date and complete_date
                    if last_sync_timestamp and 'created_date' in record and record['created_date']:
                        try:
                            created_dt = datetime.fromisoformat(record['created_date'].replace('Z', '+00:00'))
                            last_sync_dt = datetime.fromisoformat(last_sync_timestamp.replace('Z', '+00:00'))
                            if created_dt <= last_sync_dt and record.get('complete_date'):
                                logger.debug(f"Skipping finalized sprint {record['id']} with created_date {record['created_date']}")
                                continue  # Skip finalized sprints
                        except ValueError:
                            logger.warning(f"Invalid created_date: {record['created_date']}")
                    batch.append(record)
                
                if batch:
                    yield batch
                    logger.info(f"Fetched batch of {len(batch)} sprints for board {board_id}, startAt={start_at}")
                
                if data.get("isLast", True):
                    break
                start_at += data.get("maxResults", batch_size)
            except HTTPError as e:
                logger.warning(f"Error fetching sprints for board {board_id}: {str(e)}")
                raise
            finally:
                self.close()