import logging
import threading
from contextlib import contextmanager
from typing import Optional

import duckdb

from app.config import settings

logger = logging.getLogger(__name__)


class DuckDBConnectionManager:
    """Manages DuckDB connections with thread safety"""

    def __init__(self, db_path: str, read_only: bool = True, max_connections: int = 10):
        """
        Initialize the connection manager

        Args:
            db_path: Path to the DuckDB database file
            read_only: Whether to open the database in read-only mode
            max_connections: Maximum number of connections (for monitoring)
        """
        # Validate database path to prevent directory traversal
        if ".." in db_path or db_path.startswith("/"):
            raise ValueError("Invalid database path")

        self.db_path = db_path
        self.read_only = read_only
        self.max_connections = max_connections
        self._local = threading.local()
        self._main_conn: Optional[duckdb.DuckDBPyConnection] = None
        self._lock = threading.Lock()
        self._active_connections = 0

        # Initialize main connection
        self._init_main_connection()

    def _init_main_connection(self):
        """Initialize the main database connection"""
        try:
            with self._lock:
                if self._main_conn is None:
                    self._main_conn = duckdb.connect(
                        self.db_path, read_only=self.read_only
                    )
                    logger.info(f"Initialized main DuckDB connection to {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize DuckDB connection: {e}")
            raise

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """
        Get a thread-local connection using cursor pattern

        Returns:
            A thread-local DuckDB connection cursor
        """
        if not hasattr(self._local, "conn"):
            if self._main_conn is None:
                self._init_main_connection()

            if self._main_conn is None:
                raise RuntimeError("Failed to initialize database connection")

            # Create thread-local cursor
            self._local.conn = self._main_conn.cursor()
            with self._lock:
                self._active_connections += 1
            logger.debug("Created thread-local DuckDB cursor")

        return self._local.conn

    @contextmanager
    def get_connection_context(self):
        """
        Context manager for getting a connection

        Usage:
            with conn_manager.get_connection_context() as conn:
                result = conn.execute("SELECT 1")
        """
        conn = self.get_connection()
        try:
            yield conn
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            # Cleanup is handled automatically by thread-local storage
            pass

    def test_connection(self) -> bool:
        """
        Test if the database connection is working

        Returns:
            True if connection is working, False otherwise
        """
        try:
            with self.get_connection_context() as conn:
                conn.execute("SELECT 1").fetchone()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_active_connection_count(self) -> int:
        """Get the current number of active connections"""
        with self._lock:
            return self._active_connections

    def close(self):
        """Close all connections"""
        try:
            # Close thread-local connections
            if hasattr(self._local, "conn"):
                self._local.conn.close()
                with self._lock:
                    self._active_connections = max(0, self._active_connections - 1)
                delattr(self._local, "conn")

            # Close main connection
            with self._lock:
                if self._main_conn:
                    self._main_conn.close()
                    self._main_conn = None
                    self._active_connections = 0

            logger.info("Closed all DuckDB connections")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")


# Global connection manager instance
connection_manager: Optional[DuckDBConnectionManager] = None


def get_connection_manager() -> DuckDBConnectionManager:
    """Get the global connection manager instance"""
    global connection_manager
    if connection_manager is None:
        connection_manager = DuckDBConnectionManager(
            settings.database_path, settings.read_only
        )
    return connection_manager
