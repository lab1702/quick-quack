# Installation Guide

## Installation

```bash
pip install git+https://github.com/lab1702/quick-quack.git
```

## Usage

```bash
# Basic usage
quick-quack /path/to/database.duckdb

# Read-only mode (recommended for production)  
quick-quack /path/to/database.duckdb --readonly

# Custom port
quick-quack /path/to/database.duckdb --port 9000

# See all options
quick-quack --help
```

## Options

```
quick-quack [OPTIONS] DATABASE_PATH

Arguments:
  DATABASE_PATH    Path to the DuckDB database file [required]

Options:
  -r, --readonly   Open database in read-only mode
  -h, --host TEXT  Host to bind to (default: 0.0.0.0)
  -p, --port INT   Port to bind to (default: 8000)
  -w, --workers    Number of worker processes (default: 4)
  --log-level      Logging level (default: INFO)
  --reload         Enable auto-reload for development
  --version        Show version
  --help           Show help
```

## Create a Sample Database

```bash
python -c "
import duckdb
conn = duckdb.connect('sample.duckdb')
conn.execute('''
    CREATE MACRO greet(name) AS 'Hello ' || name || '!';
    CREATE MACRO add_numbers(a, b) AS a + b;
''')
conn.close()
"

# Start the server
quick-quack sample.duckdb --readonly
```

## API Access

Once running:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

For advanced configuration, see the [User Guide](docs/USER_GUIDE.md).
