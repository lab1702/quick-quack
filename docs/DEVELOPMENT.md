# Development Guide

## Development Environment Setup

### Prerequisites

- Python 3.11 or higher
- Git
- Docker (optional, for testing containers)

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd quick-quack
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Set up pre-commit hooks:**
   ```bash
   pre-commit install
   ```

5. **Create test database:**
   ```bash
   python create_test_db.py
   ```

6. **Start development server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Project Structure

```
quick-quack/
├── app/                          # Main application package
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI application and startup
│   ├── config.py                # Configuration management
│   ├── database.py              # Database connection management
│   ├── macro_service.py         # Macro discovery and execution
│   ├── api.py                   # API route handlers
│   ├── models.py                # Pydantic models
│   ├── dynamic_endpoints.py     # Dynamic endpoint generation
│   ├── monitoring.py            # Health checks and metrics
│   └── logging_config.py        # Structured logging configuration
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py              # Pytest configuration and fixtures
│   ├── test_database.py         # Database manager tests
│   ├── test_macro_service.py    # Macro service tests
│   ├── test_api.py              # API endpoint tests
│   ├── test_performance.py      # Performance tests
│   └── test_integration.py      # Integration tests
├── docs/                        # Documentation
│   ├── API.md                   # API documentation
│   ├── USER_GUIDE.md            # User guide
│   └── DEVELOPMENT.md           # This file
├── monitoring/                  # Monitoring configuration
│   ├── prometheus.yml           # Prometheus configuration
│   ├── grafana/                 # Grafana dashboards
│   └── loki.yml                 # Loki configuration
├── data/                        # Database files
├── logs/                        # Log files (created at runtime)
├── .env.example                 # Environment variable template
├── .flake8                      # Flake8 linting configuration
├── .gitignore                   # Git ignore rules
├── CHANGELOG.md                 # Version history and changes
├── CODE_REVIEW_REPORT.md        # Security and quality assessment
├── Dockerfile                   # Docker container definition
├── docker-compose.yml          # Development Docker Compose
├── docker-compose.prod.yml     # Production Docker Compose
├── mypy.ini                     # Type checking configuration
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Development dependencies
├── pytest.ini                  # Pytest configuration
└── README.md                    # Project overview
```

## Code Style and Standards

### Formatting and Linting

We enforce strict code quality standards using the following tools:

- **Black**: Code formatting (max line length: 88 chars for Python, 100 for documentation)
- **isort**: Import sorting and organization
- **Flake8**: Linting and style checking (configured for 100-character line length)
- **mypy**: Static type checking with gradual adoption

### Configuration Files

The project includes configuration files for consistent development:

- **`.flake8`**: Flake8 configuration with 100-character line length, extends ignore list
- **`mypy.ini`**: Type checking configuration with selective error handling
- **`pyproject.toml`**: Black and isort configuration (if present)

### Running Code Quality Checks

```bash
# Format code
black app tests

# Sort imports
isort app tests

# Check linting (should return 0 violations)
flake8 app tests --count --show-source --statistics

# Type checking
mypy app

# Run all checks together
black app tests && isort app tests && flake8 app tests && mypy app
```

### Code Quality Standards

Our codebase maintains **zero flake8 violations** and follows these standards:

1. **Line Length**: Maximum 100 characters for readability
2. **Import Organization**: Sorted with isort, grouped by standard/third-party/local
3. **Type Hints**: Gradual adoption with mypy configuration
4. **Documentation**: Comprehensive docstrings for all public functions
5. **Error Handling**: Consistent exception patterns with structured logging

### Security Standards

All code follows security best practices:

1. **Input Validation**: Pydantic models with regex patterns and type checking
2. **Path Validation**: Directory traversal protection for file operations
3. **CORS Configuration**: Specific origins, no wildcards in production
4. **Parameter Sanitization**: SQL injection prevention in database operations
```bash
black app tests
isort app tests
flake8 app tests
```

### Type Checking

We use **mypy** for static type checking:
```bash
mypy app
```

### Pre-commit Hooks

Pre-commit hooks automatically run formatting and linting:
```bash
pre-commit run --all-files
```

### Development Workflow

#### Before Committing
Always run the full quality check suite:
```bash
# 1. Format and organize code
black app tests
isort app tests

# 2. Check for linting violations (must be 0)
flake8 app tests --count --show-source --statistics

# 3. Run type checking
mypy app

# 4. Run tests with coverage
pytest tests/ --cov=app --cov-report=term-missing

# 5. Check security (if applicable)
bandit -r app/ -f json -o security-report.json
```

#### Continuous Integration
Our CI pipeline enforces these standards:
- **Code Quality**: Zero flake8 violations required
- **Security**: No high-severity security issues
- **Testing**: 85%+ test coverage maintained  
- **Type Safety**: MyPy checks pass (with configured ignores)

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m performance

# Run with coverage
pytest --cov=app --cov-report=html

# Run tests in parallel
pytest -n auto

# Skip slow tests
pytest -m "not slow"
```

### Test Categories

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test component interactions
- **Performance tests**: Test performance and load handling
- **End-to-end tests**: Test complete workflows

### Writing Tests

#### Unit Test Example

```python
import pytest
from app.macro_service import MacroService

@pytest.mark.asyncio
async def test_list_macros(test_macro_service: MacroService):
    """Test listing all available macros."""
    macros = await test_macro_service.list_macros()
    
    assert len(macros) >= 5
    assert all(macro.name for macro in macros)
```

#### Integration Test Example

```python
def test_complete_workflow(test_client: TestClient):
    """Test a complete API workflow."""
    # Check health
    health_response = test_client.get("/health")
    assert health_response.status_code == 200
    
    # List macros
    macros_response = test_client.get("/api/v1/macros")
    assert macros_response.status_code == 200
    
    # Execute macro
    exec_response = test_client.post(
        "/api/v1/macros/greet/execute",
        json={"name": "Test"}
    )
    assert exec_response.status_code == 200
```

### Test Fixtures

Key test fixtures are defined in `tests/conftest.py`:

- `test_db_path`: Temporary test database
- `test_settings`: Test configuration
- `test_client`: FastAPI test client
- `test_database_manager`: Database manager instance
- `test_macro_service`: Macro service instance

## Architecture and Design Patterns

### Component Overview

#### Database Manager (`app/database.py`)
- Manages DuckDB connections using thread-local storage
- Provides connection pooling and health checking
- Handles both read-only and read-write modes

#### Macro Service (`app/macro_service.py`)
- Discovers macros using DuckDB's introspection capabilities
- Caches macro metadata for performance
- Handles macro execution with parameter validation

#### API Layer (`app/api.py`)
- Provides RESTful endpoints for macro operations
- Handles request/response serialization
- Implements error handling and validation

#### Dynamic Endpoints (`app/dynamic_endpoints.py`)
- Generates FastAPI routes dynamically based on available macros
- Creates both GET and POST endpoints for each macro
- Handles parameter binding and validation

#### Monitoring (`app/monitoring.py`)
- Provides health check endpoints
- Collects system and application metrics
- Exports Prometheus-compatible metrics

### Key Design Decisions

1. **Thread-local connections**: Each thread gets its own DuckDB cursor for thread safety
2. **Macro caching**: Macro metadata is cached on startup for performance
3. **Dynamic routing**: Routes are generated dynamically based on discovered macros
4. **Structured logging**: JSON logging with correlation IDs for observability
5. **Health checks**: Multiple levels of health checks for different use cases

### Error Handling Strategy

1. **Validation errors**: Return 422 with detailed error information
2. **Not found errors**: Return 404 for missing macros
3. **Execution errors**: Return 500 with sanitized error messages
4. **All errors**: Include correlation IDs for tracking

## Adding New Features

### Adding a New Endpoint

1. **Define the route in `app/api.py`:**
   ```python
   @router.get("/new-endpoint")
   async def new_endpoint():
       return {"message": "Hello from new endpoint"}
   ```

2. **Add tests in `tests/test_api.py`:**
   ```python
   def test_new_endpoint(test_client: TestClient):
       response = test_client.get("/new-endpoint")
       assert response.status_code == 200
   ```

3. **Update documentation in `docs/API.md`**

### Adding New Configuration

1. **Add to Settings class in `app/config.py`:**
   ```python
   class Settings(BaseSettings):
       new_setting: str = "default_value"
   ```

2. **Use in application code:**
   ```python
   from app.config import get_settings
   
   settings = get_settings()
   value = settings.new_setting
   ```

3. **Update `.env.example` with new variable**
4. **Document in `docs/USER_GUIDE.md`**

### Adding New Monitoring Metrics

1. **Define metric in `app/monitoring.py`:**
   ```python
   from prometheus_client import Counter
   
   new_metric = Counter('duckdb_rest_new_metric_total', 'Description')
   ```

2. **Update metric in code:**
   ```python
   new_metric.inc()  # Increment counter
   ```

3. **Include in metrics endpoint**

## Database Schema and Macros

### Test Database Schema

The test database includes:

```sql
-- Employees table
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    department VARCHAR,
    salary DECIMAL(10,2),
    hire_date DATE
);

-- Sample macros
CREATE MACRO greet(name) AS 
SELECT 'Hello, ' || name || '!' as greeting;

CREATE MACRO employees_by_department(dept) AS 
SELECT * FROM employees WHERE department = dept;

CREATE MACRO high_earners(min_salary) AS 
SELECT name, salary FROM employees 
WHERE salary >= min_salary 
ORDER BY salary DESC;
```

### Macro Guidelines

1. **Naming**: Use descriptive, snake_case names
2. **Parameters**: Clearly define parameter types
3. **Return values**: Consider the API response format
4. **Performance**: Optimize for expected data sizes
5. **Documentation**: Add comments for complex logic

## Debugging and Development Tools

### Debug Configuration

Set debug environment variables:
```bash
export DUCKDB_REST_LOG_LEVEL=DEBUG
export DUCKDB_REST_JSON_LOGGING=false  # Easier to read during development
```

### Interactive Development

Use the FastAPI automatic reload feature:
```bash
uvicorn app.main:app --reload
```

### Database Inspection

Inspect macros directly in DuckDB:
```sql
-- List all macros
SELECT * FROM duckdb_functions() WHERE function_type = 'macro';

-- Show macro definition
SELECT function_name, macro_definition 
FROM duckdb_functions() 
WHERE function_name = 'your_macro_name';
```

### API Testing

Use the interactive API docs:
- Development: http://localhost:8000/docs
- Alternative: http://localhost:8000/redoc

### Log Analysis

Enable structured logging and use `jq` for analysis:
```bash
# Filter by log level
tail -f logs/app.log | jq 'select(.level == "ERROR")'

# Filter by correlation ID
tail -f logs/app.log | jq 'select(.correlation_id == "abc-123")'

# Monitor performance
tail -f logs/app.log | jq 'select(.message | contains("executed")) | {macro: .extra.macro_name, duration: .extra.duration_ms}'
```

## Performance Optimization

### Database Performance

1. **Indexing**: Add indexes for commonly filtered columns
2. **Query optimization**: Review generated SQL for performance
3. **Connection pooling**: Monitor connection usage
4. **Read-only mode**: Use when possible to reduce locking

### Application Performance

1. **Macro caching**: Metadata is cached on startup
2. **Connection reuse**: Thread-local connections reduce overhead
3. **Async operations**: Use async/await for I/O operations
4. **Response streaming**: Consider for large result sets

### Monitoring Performance

Use the metrics endpoint to monitor:
- Request latency
- Memory usage
- Active connections
- Error rates

## Security Considerations

### Input Validation

1. **Parameter validation**: All inputs are validated with Pydantic
2. **SQL injection protection**: Parameterized queries only
3. **Macro name validation**: Strict naming rules enforced

### Database Security

1. **Read-only mode**: Use when possible
2. **File permissions**: Restrict database file access
3. **Network isolation**: Limit database network exposure

### Application Security

1. **Error handling**: Don't expose internal details
2. **Request limiting**: Consider rate limiting for production
3. **Logging**: Log security events without exposing sensitive data

## Deployment and Operations

### Environment Management

Use different configurations for different environments:
- `.env.development`
- `.env.staging`  
- `.env.production`

### Container Best Practices

1. **Multi-stage builds**: Reduce image size
2. **Non-root user**: Run as non-privileged user
3. **Health checks**: Include health check in Dockerfile
4. **Security scanning**: Scan images for vulnerabilities

### Monitoring and Alerting

Set up alerts for:
- Health check failures
- High error rates
- Memory/CPU usage
- Response time degradation

## Contributing Guidelines

### Before Contributing

1. **Read documentation**: Understand the project structure and goals
2. **Check issues**: Look for existing issues or feature requests
3. **Discuss major changes**: Open an issue for significant modifications

### Development Workflow

1. **Create feature branch**: `git checkout -b feature/new-feature`
2. **Write tests**: Add tests for new functionality
3. **Run test suite**: Ensure all tests pass
4. **Update documentation**: Update relevant documentation
5. **Submit pull request**: Include clear description of changes

### Code Review Process

1. **Automated checks**: CI pipeline runs tests and linting
2. **Manual review**: Code review by maintainers
3. **Documentation review**: Ensure documentation is updated
4. **Integration testing**: Test in staging environment

### Commit Guidelines

Use conventional commit messages:
```
feat: add new health check endpoint
fix: resolve connection pool leak
docs: update API documentation
test: add integration tests for monitoring
```

## Troubleshooting Development Issues

### Common Development Problems

1. **Import errors**: Check Python path and virtual environment
2. **Database locks**: Ensure proper connection cleanup
3. **Test failures**: Check test database setup and fixtures
4. **Performance issues**: Profile code and check query performance

### Debug Tools

1. **Python debugger**: Use `pdb` or IDE debugger
2. **DuckDB CLI**: Query database directly
3. **curl/httpie**: Test API endpoints manually
4. **Docker logs**: Check container logs for issues

For additional development support, refer to:
- Project issue tracker
- API documentation
- Test examples in the test suite
