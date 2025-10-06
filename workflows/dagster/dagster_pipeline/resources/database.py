# resources/database.py
from dagster import ConfigurableResource
from typing import Optional
import mysql.connector
import clickhouse_connect
import psycopg2
from contextlib import contextmanager

class MySQLResource(ConfigurableResource):
    """MySQL resource supporting connections to specified databases"""
    host: str
    port: int = 3306
    user: str
    password: str
    
    @contextmanager
    def get_connection(self, database: str):
        """
        Get connection to a specific database
        
        Args:
            database: Database name to connect to
        """
        conn = mysql.connector.connect(
            host=self.host,
            port=self.port,
            database=database,
            user=self.user,
            password=self.password
        )
        try:
            yield conn
        finally:
            conn.close()


class ClickHouseResource(ConfigurableResource):
    """ClickHouse resource supporting connections to specified databases"""
    host: str
    port: int = 8443
    user: str
    password: str
    secure: bool = True
    
    @contextmanager
    def get_client(self, database: str):
        """
        Get client connected to a specific database
        
        Args:
            database: Database name to connect to
        """
        client = clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            database=database,
            secure=self.secure
        )
        try:
            yield client
        finally:
            client.close()


class PostgreSQLResource(ConfigurableResource):
    """PostgreSQL resource supporting connections to specified databases"""
    host: str
    port: int = 5432
    user: str
    password: str
    
    @contextmanager
    def get_connection(self, database: str):
        """
        Get connection to a specific database
        
        Args:
            database: Database name to connect to
        """
        conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=database,
            user=self.user,
            password=self.password
        )
        try:
            yield conn
        finally:
            conn.close()