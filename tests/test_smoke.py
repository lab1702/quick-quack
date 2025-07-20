"""
Basic smoke test to verify test infrastructure.
"""
import pytest
import tempfile
import os
import duckdb
from app.config import Settings
from app.database import DuckDBConnectionManager


def test_basic_setup():
    """Test that basic test setup works."""
    assert True


def test_settings_creation():
    """Test creating test settings."""
    settings = Settings(
        database_path=":memory:",
        read_only=False,
        log_level="DEBUG"
    )
    assert settings.database_path == ":memory:"
    assert settings.read_only is False
    assert settings.log_level == "DEBUG"


def test_database_manager_creation():
    """Test creating database manager with in-memory database."""
    manager = DuckDBConnectionManager(":memory:", read_only=False)
    
    try:
        conn = manager.get_connection()
        result = conn.execute("SELECT 1 as test").fetchone()
        assert result[0] == 1
    finally:
        manager.close()


def test_duckdb_macro_creation():
    """Test creating and using a macro in DuckDB."""
    conn = duckdb.connect(":memory:")
    
    # Create a simple scalar macro
    conn.execute("CREATE MACRO test_macro(x) AS x * 2")
    
    # Test the macro
    result = conn.execute("SELECT test_macro(5)").fetchone()
    assert result[0] == 10
    
    # List macros
    macros = conn.execute("""
        SELECT function_name 
        FROM duckdb_functions() 
        WHERE function_type = 'macro' AND function_name = 'test_macro'
    """).fetchall()
    
    assert len(macros) == 1
    assert macros[0][0] == "test_macro"
    
    conn.close()
