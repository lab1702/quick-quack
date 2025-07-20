# User Guide

## Installation & Deployment

### Basic Installation

```bash
pip install git+https://github.com/lab1702/quick-quack.git
quick-quack /path/to/database.duckdb --readonly
```

### Docker

```bash
docker build -t quick-quack .
docker run -p 8000:8000 -v ./data:/app/data quick-quack
```

### Production

```bash
# Using gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Using CLI
quick-quack /path/to/database.duckdb --readonly --workers 4
```

## Configuration

### Command Line Options

```bash
quick-quack database.duckdb --readonly --host localhost --port 8080
```

### Environment Variables

```bash
export DUCKDB_REST_DATABASE_PATH="/path/to/database.duckdb"
export DUCKDB_REST_READ_ONLY="true"
export DUCKDB_REST_HOST="0.0.0.0"
export DUCKDB_REST_PORT="8000"
```

### Key Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DUCKDB_REST_DATABASE_PATH` | `data/macros.db` | Path to DuckDB database file |
| `DUCKDB_REST_READ_ONLY` | `true` | Whether to open database in read-only mode |
| `DUCKDB_REST_HOST` | `0.0.0.0` | Host to bind the server |
| `DUCKDB_REST_PORT` | `8000` | Port to bind the server |
| `DUCKDB_REST_LOG_LEVEL` | `INFO` | Logging level |

## Using Macros

### Create Macros in DuckDB

```sql
-- Simple macro
CREATE MACRO greet(name) AS 'Hello, ' || name || '!';

-- Table macro  
CREATE MACRO recent_sales(days) AS 
TABLE SELECT * FROM sales WHERE sale_date >= current_date - interval days day;
```

### Call Macros via API

```bash
# List all macros
curl http://localhost:8000/api/v1/macros

# Execute a macro
curl -X POST "http://localhost:8000/api/v1/macros/greet/execute" \
  -H "Content-Type: application/json" \
  -d '{"name": "World"}'
```

## Monitoring

```bash
# Health check
curl http://localhost:8000/health

# Metrics  
curl http://localhost:8000/metrics
```

For complete API documentation, see the interactive docs at http://localhost:8000/docs
