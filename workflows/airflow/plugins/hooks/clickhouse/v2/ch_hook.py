from airflow.hooks.base import BaseHook
import clickhouse_connect
from clickhouse_connect.driver.client import Client

from plugins.utils.defaults.v1.defaults import LOG_LEVELS

class ClickHouseCloudHook(BaseHook):
    def test_ch_connection():
        """
        Test the connection to ClickHouse.
        
        :return: True if the connection is successful, False otherwise
        """
    def ch_db_table_exists(self, db_name: str, table_name: str) -> bool:
        """
        Check if a ClickHouse table exists in a specific database.
        
        :param db_name: Name of the database
        :param table_name: Name of the table to check
        :return: True if the table exists, False otherwise
        """
    def fetch_ch_table_data(self, db_name: str, table_name: str, limit: int = 100) -> list:
        """
        Fetch data from a ClickHouse table.
        
        :param db_name: Name of the database
        :param table_name: Name of the table to fetch data from
        :param limit: Maximum number of rows to fetch
        :return: List of rows fetched from the table
        """
    def close(self) -> None:
        """
        Close the connection to ClickHouse if it exists.
        """