"""
Tests for the CLI module.
"""

import tempfile
import os
from pathlib import Path
from click.testing import CliRunner
from app.cli import main
import duckdb


def test_cli_help():
    """Test that the CLI help command works."""
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'quick-quack' in result.output
    assert 'DATABASE_PATH' in result.output
    assert '--readonly' in result.output


def test_cli_version():
    """Test that the CLI version command works."""
    runner = CliRunner()
    result = runner.invoke(main, ['--version'])
    assert result.exit_code == 0
    assert '1.0.0' in result.output


def test_cli_with_nonexistent_database():
    """Test that the CLI fails gracefully with a nonexistent database."""
    runner = CliRunner()
    result = runner.invoke(main, ['/nonexistent/path/database.duckdb'])
    assert result.exit_code == 1
    assert 'does not exist' in result.output


def test_cli_environment_variables():
    """Test that CLI sets environment variables correctly."""
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix='.duckdb', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        # Create a simple database
        conn = duckdb.connect(db_path)
        conn.execute("CREATE MACRO test_macro() AS 'Hello World'")
        conn.close()
        
        # Mock the uvicorn.run function to avoid starting the actual server
        import app.cli
        original_uvicorn_run = app.cli.uvicorn.run
        
        def mock_uvicorn_run(*args, **kwargs):
            # Just verify the environment variables are set correctly
            assert os.environ.get('DUCKDB_REST_DATABASE_PATH') == str(Path(db_path).resolve())
            assert os.environ.get('DUCKDB_REST_READ_ONLY') == 'true'
            assert os.environ.get('DUCKDB_REST_HOST') == 'localhost'
            assert os.environ.get('DUCKDB_REST_PORT') == '9000'
            raise KeyboardInterrupt()  # Exit immediately to avoid starting server
        
        app.cli.uvicorn.run = mock_uvicorn_run
        
        runner = CliRunner()
        result = runner.invoke(main, [
            db_path, 
            '--readonly', 
            '--host', 'localhost', 
            '--port', '9000'
        ])
        
        # Should exit with 0 due to KeyboardInterrupt handling
        assert result.exit_code == 0
        
        # Restore original function
        app.cli.uvicorn.run = original_uvicorn_run
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_cli_readonly_flag():
    """Test that the readonly flag works correctly."""
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix='.duckdb', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        # Create a simple database
        conn = duckdb.connect(db_path)
        conn.execute("CREATE MACRO test_macro() AS 'Hello World'")
        conn.close()
        
        # Mock uvicorn.run to check environment variables
        import app.cli
        original_uvicorn_run = app.cli.uvicorn.run
        
        def mock_uvicorn_run(*args, **kwargs):
            assert os.environ.get('DUCKDB_REST_READ_ONLY') == 'false'
            raise KeyboardInterrupt()
        
        app.cli.uvicorn.run = mock_uvicorn_run
        
        runner = CliRunner()
        # Test without readonly flag (should default to False)
        result = runner.invoke(main, [db_path])
        assert result.exit_code == 0
        
        # Restore original function
        app.cli.uvicorn.run = original_uvicorn_run
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)
