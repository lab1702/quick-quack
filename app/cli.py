"""
Command-line interface for quick-quack DuckDB Macro REST Server.
"""

import sys
from pathlib import Path

import click
import uvicorn


@click.command()
@click.argument('database_path', type=click.Path(exists=True), required=True)
@click.option('--readonly', '-r', is_flag=True, default=False, 
              help='Open database in read-only mode (default: False)')
@click.option('--host', '-h', default='0.0.0.0', 
              help='Host to bind the server to (default: 0.0.0.0)')
@click.option('--port', '-p', default=8000, type=int,
              help='Port to bind the server to (default: 8000)')
@click.option('--workers', '-w', default=4, type=int,
              help='Number of worker processes (default: 4)')
@click.option('--log-level', default='INFO', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'], case_sensitive=False),
              help='Logging level (default: INFO)')
@click.option('--reload', is_flag=True, default=False,
              help='Enable auto-reload for development (default: False)')
@click.version_option(version='1.0.0', prog_name='quick-quack')
def main(database_path: str, readonly: bool, host: str, port: int, workers: int, 
         log_level: str, reload: bool):
    """
    Start the quick-quack DuckDB Macro REST Server.
    
    DATABASE_PATH: Path to the DuckDB database file to serve macros from.
    
    Examples:
        quick-quack /path/to/database.duckdb
        quick-quack /path/to/database.duckdb --readonly
        quick-quack /path/to/database.duckdb --port 8080 --host localhost
    """
    # Convert path to absolute path
    db_path = Path(database_path).resolve()
    
    if not db_path.exists():
        click.echo(f"Error: Database file does not exist: {db_path}", err=True)
        sys.exit(1)
    
    # Set environment variables for the application
    import os
    os.environ['DUCKDB_REST_DATABASE_PATH'] = str(db_path)
    os.environ['DUCKDB_REST_READ_ONLY'] = str(readonly).lower()
    os.environ['DUCKDB_REST_HOST'] = host
    os.environ['DUCKDB_REST_PORT'] = str(port)
    os.environ['DUCKDB_REST_WORKERS'] = str(workers)
    os.environ['DUCKDB_REST_LOG_LEVEL'] = log_level.upper()
    
    click.echo(f"Starting quick-quack server...")
    click.echo(f"Database: {db_path}")
    click.echo(f"Read-only: {readonly}")
    click.echo(f"Host: {host}")
    click.echo(f"Port: {port}")
    click.echo(f"Log level: {log_level}")
    
    if reload:
        click.echo("Auto-reload enabled (development mode)")
    
    click.echo(f"Server will be available at: http://{host}:{port}")
    click.echo(f"API docs will be available at: http://{host}:{port}/docs")
    click.echo("")
    
    try:
        # Start the server
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level.lower(),
            workers=1 if reload else workers,  # Use single worker in reload mode
        )
    except KeyboardInterrupt:
        click.echo("\nShutting down server...")
    except Exception as e:
        click.echo(f"Error starting server: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
