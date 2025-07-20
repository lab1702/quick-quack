# DuckDB Macro REST Server

A REST API server that exposes DuckDB macros as HTTP endpoints with automatic discovery and dynamic routing.

## 🚀 Quick Start

### Installation

```bash
pip install git+https://github.com/lab1702/quick-quack.git
```

### Basic Usage

```bash
# Start server with a DuckDB database
quick-quack /path/to/database.duckdb

# Start in read-only mode (recommended)
quick-quack /path/to/database.duckdb --readonly
```

### Create a Test Database

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

### Test the API

```bash
# API docs: http://localhost:8000/docs
curl -X POST "http://localhost:8000/api/v1/macros/greet/execute" \
  -H "Content-Type: application/json" -d '{"name": "World"}'
```

## ✨ Key Features

- **Automatic Discovery**: Finds all macros in your DuckDB database
- **REST API**: GET and POST endpoints for each macro
- **Parameter Validation**: Automatic type checking and validation
- **Read-only Mode**: Safe production deployment
- **Health Monitoring**: Built-in health checks and metrics

## 📖 Documentation

- **[Installation Guide](INSTALL.md)** - CLI installation and usage
- **[User Guide](docs/USER_GUIDE.md)** - Configuration and deployment  
- **[API Reference](docs/API.md)** - Complete API documentation

## License

MIT License - see [LICENSE](LICENSE) file for details.
