"""
Unit tests for the DuckDB database manager.
"""
import pytest
import tempfile
import os
import duckdb
from app.database import DuckDBConnectionManager
from app.config import Settings


class TestDuckDBConnectionManager:
    """Test suite for DuckDBConnectionManager class."""
    
    def test_initialization(self, test_settings: Settings):
        """Test database manager initialization."""
        manager = DuckDBConnectionManager(test_settings.database_path, test_settings.read_only)
        assert manager.db_path == test_settings.database_path
        assert manager.read_only == test_settings.read_only
        manager.close()
    
    def test_connection_creation(self, test_database_manager: DuckDBConnectionManager):
        """Test that connections are created successfully."""
        conn = test_database_manager.get_connection()
        assert conn is not None
        
        # Test connection works
        result = conn.execute("SELECT 1 as test").fetchone()
        assert result[0] == 1
    
    def test_connection_reuse(self, test_database_manager: DuckDBConnectionManager):
        """Test that connections are reused within same thread."""
        conn1 = test_database_manager.get_connection()
        conn2 = test_database_manager.get_connection()
        
        # Should be the same connection object in same thread
        assert conn1 is conn2
    
    def test_read_only_mode(self, test_db_path: str):
        """Test read-only connection prevents writes."""
        manager = DuckDBConnectionManager(test_db_path, read_only=True)
        
        try:
            conn = manager.get_connection()
            
            # Should be able to read
            result = conn.execute("SELECT COUNT(*) FROM employees").fetchone()
            assert result[0] == 5
            
            # Should not be able to write (this may vary by DuckDB version)
            with pytest.raises(Exception):
                conn.execute("INSERT INTO employees VALUES (6, 'Test', 'Test', 50000, '2024-01-01')")
                
        finally:
            manager.close()
    
    def test_database_health_check(self, test_database_manager: DuckDBConnectionManager):
        """Test database health check functionality."""
        is_healthy = test_database_manager.test_connection()
        assert is_healthy is True
    
    def test_database_health_check_with_invalid_db(self):
        """Test health check with invalid database."""
        manager = DuckDBConnectionManager("/nonexistent/path.duckdb", read_only=True)
        
        try:
            is_healthy = manager.test_connection()
            assert is_healthy is False
        finally:
            manager.close()
    
    def test_connection_pool_stats(self, test_database_manager: DuckDBConnectionManager):
        """Test connection pool statistics."""
        # Get a connection first
        conn = test_database_manager.get_connection()
        assert conn is not None
        
        # Test the available method
        active_count = test_database_manager.get_active_connection_count()
        assert active_count >= 0
        assert isinstance(stats["connection_pool_healthy"], bool)
    
    def test_close_connections(self, test_database_manager: DuckDBConnectionManager):
        """Test closing all connections."""
        # Create a connection
        conn = test_database_manager.get_connection()
        assert conn is not None
        
        # Close all connections
        test_database_manager.close()
        
        # Verify connection pool stats show no active connections
        stats = test_database_manager.get_connection_pool_stats()
        assert stats["active_connections"] == 0
    
    def test_execute_query_method(self, test_database_manager: DuckDBConnectionManager):
        """Test the execute_query helper method."""
        result = test_database_manager.execute_query(
            "SELECT name, department FROM employees WHERE id = ?", 
            (1,)
        )
        
        assert len(result) == 1
        assert result[0]["name"] == "Alice Johnson"
        assert result[0]["department"] == "Engineering"
    
    def test_execute_query_with_error(self, test_database_manager: DuckDBConnectionManager):
        """Test execute_query with SQL error."""
        with pytest.raises(Exception):
            test_database_manager.execute_query("SELECT * FROM nonexistent_table")
    
    def test_concurrent_connections(self, test_database_manager: DuckDBConnectionManager):
        """Test that multiple connections work correctly."""
        import threading
        import time
        
        results = []
        errors = []
        
        def query_worker(worker_id):
            try:
                conn = test_database_manager.get_connection()
                result = conn.execute(f"SELECT {worker_id} as worker_id, COUNT(*) as count FROM employees").fetchone()
                results.append((worker_id, result))
                time.sleep(0.1)  # Simulate some work
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=query_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors in concurrent access: {errors}"
        assert len(results) == 5
        
        for worker_id, result in results:
            assert result[0] == worker_id  # worker_id
            assert result[1] == 5  # employee count


class TestDuckDBConnectionManagerErrorHandling:
    """Test error handling in DuckDBConnectionManager."""
    
    def test_invalid_database_path(self):
        """Test handling of invalid database path."""
        settings = Settings(database_path="/invalid/path/database.duckdb")
        manager = DuckDBConnectionManager(settings)
        
        with pytest.raises(Exception):
            manager.get_connection()
        
        manager.close()
    
    def test_corrupted_database_handling(self):
        """Test handling of corrupted database file."""
        # Create a corrupted database file
        with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as tmp_file:
            tmp_file.write(b"This is not a valid DuckDB file")
            corrupted_path = tmp_file.name
        
        try:
            settings = Settings(database_path=corrupted_path)
            manager = DuckDBConnectionManager(settings)
            
            with pytest.raises(Exception):
                manager.get_connection()
            
            manager.close()
        finally:
            os.unlink(corrupted_path)
