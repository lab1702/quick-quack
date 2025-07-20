"""
Pytest configuration and fixtures for DuckDB Macro REST Server tests.
"""
import os
import pytest
import tempfile
import duckdb
from pathlib import Path
from typing import Generator
from fastapi.testclient import TestClient
from app.main import app
from app.database import DuckDBConnectionManager
from app.macro_service import MacroIntrospectionService
from app.config import Settings


@pytest.fixture(scope="session")
def test_db_path() -> Generator[str, None, None]:
    """Create a temporary test database with sample macros."""
    # Create a temporary file path without creating the file
    import tempfile
    import os
    
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_database.duckdb")
    
    try:
        # Create test database with sample data and macros
        conn = duckdb.connect(db_path)
        
        # Create sample table
        conn.execute("""
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                name VARCHAR,
                department VARCHAR,
                salary DECIMAL(10,2),
                hire_date DATE
            )
        """)
        
        # Insert sample data
        conn.execute("""
            INSERT INTO employees VALUES
            (1, 'Alice Johnson', 'Engineering', 75000.00, '2022-01-15'),
            (2, 'Bob Smith', 'Sales', 65000.00, '2021-06-01'),
            (3, 'Carol Davis', 'Engineering', 80000.00, '2020-03-10'),
            (4, 'David Wilson', 'Marketing', 55000.00, '2023-02-20'),
            (5, 'Eva Brown', 'Sales', 70000.00, '2022-08-05')
        """)
        
        # Create test macros
        test_macros = [
            "CREATE MACRO greet(name) AS CONCAT('Hello, ', name, '!')",
            "CREATE MACRO employees_by_department(dept) AS TABLE SELECT * FROM employees WHERE department = dept",
            "CREATE MACRO high_earners(min_salary) AS TABLE SELECT name, salary FROM employees WHERE salary >= min_salary ORDER BY salary DESC",
            "CREATE MACRO employee_count() AS TABLE SELECT COUNT(*) as total_employees FROM employees",
            "CREATE MACRO salary_stats() AS TABLE SELECT MIN(salary) as min_salary, MAX(salary) as max_salary, AVG(salary) as avg_salary, COUNT(*) as employee_count FROM employees"
        ]
        
        for macro_sql in test_macros:
            conn.execute(macro_sql)
        
        # Properly close connection before yielding
        conn.close()
        yield db_path
        
    except Exception as e:
        # Make sure connection is closed on error
        try:
            conn.close()
        except:
            pass
        raise e
    finally:
        # Cleanup with retry for Windows file locking issues
        import shutil
        import time
        
        # Wait a bit for file handles to be released
        time.sleep(0.1)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                break
            except PermissionError:
                if attempt < max_retries - 1:
                    time.sleep(0.5)  # Wait longer before retry
                    continue
                else:
                    # If all retries fail, just print a warning
                    print(f"Warning: Could not clean up test database directory: {temp_dir}")
                    break


@pytest.fixture
def test_settings(test_db_path: str) -> Settings:
    """Create test settings with temporary database."""
    return Settings(
        database_path=test_db_path,
        read_only=True,
        log_level="DEBUG",
        json_logging=False  # Easier to read in tests
    )


@pytest.fixture
def test_database_manager(test_settings: Settings) -> Generator[DuckDBConnectionManager, None, None]:
    """Create a test database manager."""
    manager = DuckDBConnectionManager(
        test_settings.database_path, 
        test_settings.read_only
    )
    try:
        yield manager
    finally:
        manager.close()


@pytest.fixture
def test_macro_service(test_database_manager: DuckDBConnectionManager) -> MacroIntrospectionService:
    """Create a test macro service."""
    return MacroIntrospectionService(test_database_manager)


@pytest.fixture
def test_client(test_settings: Settings) -> Generator[TestClient, None, None]:
    """Create a test client with temporary database."""
    # Override settings for testing
    app.dependency_overrides = {}
    
    # Create test client
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_macro_execution_data():
    """Sample data for macro execution tests."""
    return {
        "greet": [
            {"name": "Alice"},
            {"name": "Bob"},
            {"name": "World"}
        ],
        "employees_by_department": [
            {"dept": "Engineering"},
            {"dept": "Sales"},
            {"dept": "Marketing"}
        ],
        "high_earners": [
            {"min_salary": 60000},
            {"min_salary": 75000},
            {"min_salary": 90000}
        ]
    }


@pytest.fixture
def expected_macro_results():
    """Expected results for macro execution tests."""
    return {
        "employee_count": [{"total_employees": 5}],
        "salary_stats": [{
            "min_salary": 55000.0,
            "max_salary": 80000.0,
            "avg_salary": 69000.0,
            "employee_count": 5
        }]
    }


# Test data fixtures
@pytest.fixture
def invalid_macro_names():
    """List of invalid macro names for testing."""
    return [
        "nonexistent_macro",
        "DROP TABLE employees",
        "'; DROP TABLE employees; --",
        "../../../etc/passwd",
        "macro_with_spaces in name"
    ]


@pytest.fixture
def performance_test_params():
    """Parameters for performance testing."""
    return {
        "concurrent_requests": [1, 5, 10, 20],
        "request_count": 100,
        "timeout_seconds": 30
    }
