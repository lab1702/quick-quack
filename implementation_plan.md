# Detailed Implementation Plan for DuckDB Macro REST Server

Based on comprehensive research into DuckDB capabilities, web frameworks, architectural patterns, and production best practices, here's a detailed implementation plan for building a RESTful server that exposes DuckDB macros as HTTP endpoints.

## Recommended Technology Stack

**Python 3.11+ with FastAPI** emerges as the optimal choice based on:
- **Excellent DuckDB integration** with mature Python bindings supporting both sync and async operations
- **Superior developer experience** with automatic API documentation, type validation, and dependency injection  
- **Rich ecosystem** with proven middleware for production deployments
- **Sufficient performance** (~42,000 req/s) for most analytical workloads where database query time dominates

### Core Dependencies
```python
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
duckdb==1.3.2
pydantic==2.5.0
python-multipart==0.0.6
gunicorn==21.2.0
```

## High-Level Architecture Design

### Component Overview
```
┌─────────────────────┐
│   HTTP Client       │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   FastAPI Server    │
│  ┌───────────────┐  │
│  │ Macro Router  │  │
│  ├───────────────┤  │
│  │ Introspection │  │
│  │   Service     │  │
│  ├───────────────┤  │
│  │  Connection   │  │
│  │   Manager     │  │
│  └───────────────┘  │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   DuckDB Database   │
│   (with macros)     │
└─────────────────────┘
```

### Key Implementation Components

#### 1. DuckDB Connection Manager
```python
class DuckDBConnectionManager:
    """Manages DuckDB connections with thread safety and pooling"""
    
    def __init__(self, db_path: str, read_only: bool = True):
        self.db_path = db_path
        self.read_only = read_only
        self._local = threading.local()
    
    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get thread-local connection using cursor() pattern"""
        if not hasattr(self._local, 'conn'):
            # Main connection
            if not hasattr(self, '_main_conn'):
                self._main_conn = duckdb.connect(
                    self.db_path, 
                    read_only=self.read_only
                )
            # Thread-local cursor
            self._local.conn = self._main_conn.cursor()
        return self._local.conn
```

#### 2. Macro Introspection Service
```python
class MacroIntrospectionService:
    """Discovers and analyzes DuckDB macros"""
    
    async def list_macros(self, conn: duckdb.DuckDBPyConnection) -> List[MacroInfo]:
        """Query duckdb_functions() to find all macros"""
        query = """
        SELECT 
            function_name,
            parameters,
            parameter_types,
            return_type,
            macro_definition
        FROM duckdb_functions()
        WHERE function_type = 'macro' 
          AND internal = false
        ORDER BY function_name
        """
        result = conn.execute(query).fetchall()
        return [self._parse_macro(row) for row in result]
    
    def _parse_macro(self, row) -> MacroInfo:
        """Parse macro metadata into structured format"""
        return MacroInfo(
            name=row[0],
            parameters=row[1],
            parameter_types=row[2],
            return_type=row[3],
            is_table_macro='TABLE' in row[4]
        )
```

#### 3. Dynamic Endpoint Generator
```python
class MacroEndpointGenerator:
    """Creates FastAPI endpoints for each discovered macro"""
    
    def create_endpoint(self, macro_info: MacroInfo, conn_manager: DuckDBConnectionManager):
        """Generate endpoint function for a macro"""
        
        async def macro_endpoint(**kwargs):
            conn = conn_manager.get_connection()
            
            # Build parameter list
            params = []
            for param_name, param_type in zip(macro_info.parameters, macro_info.parameter_types):
                if param_name in kwargs:
                    params.append(self._convert_parameter(kwargs[param_name], param_type))
            
            # Execute macro
            query = f"SELECT * FROM {macro_info.name}({','.join(['?' for _ in params])})"
            try:
                result = conn.execute(query, params)
                if macro_info.is_table_macro:
                    return {"data": result.fetchall(), "columns": result.description}
                else:
                    return {"result": result.fetchone()[0]}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        return macro_endpoint
```

## API Endpoint Design Patterns

### Base Endpoints

**Macro Discovery**
```
GET /api/v1/macros
Response: List of available macros with metadata
```

**Macro Details**
```
GET /api/v1/macros/{macro_name}
Response: Detailed information about specific macro including parameters
```

**Macro Execution**
```
POST /api/v1/macros/{macro_name}/execute
Body: JSON with parameter values
Response: Macro execution results
```

### Dynamic Endpoints (Optional)
```
GET /api/v1/{macro_name}?param1=value1&param2=value2
POST /api/v1/{macro_name} with JSON body for complex parameters
```

### System Endpoints
```
GET /health - Health check with database connectivity test
GET /metrics - Prometheus-compatible metrics
GET /api/v1/openapi.json - OpenAPI specification
```

## Configuration and Deployment Approach

### Configuration Structure
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database configuration
    database_path: str = "data/database.duckdb"
    read_only: bool = True
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # Performance settings
    connection_timeout: int = 30
    query_timeout: int = 300
    max_result_size: int = 10000
    
    class Config:
        env_prefix = "DUCKDB_REST_"
        env_file = ".env"
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=appuser:appuser . .

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health').raise_for_status()"

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

## Error Handling Strategies

### Structured Error Responses
```python
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict] = None
    request_id: str

@app.exception_handler(DuckDBException)
async def duckdb_exception_handler(request: Request, exc: DuckDBException):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="database_error",
            message="Database operation failed",
            details={"query_error": str(exc)},
            request_id=request.state.request_id
        ).dict()
    )
```

### Error Categories
- **400 Bad Request**: Invalid parameters, type mismatches
- **404 Not Found**: Macro doesn't exist
- **408 Request Timeout**: Query execution timeout
- **500 Internal Server Error**: Database errors, unexpected failures
- **503 Service Unavailable**: Database connection issues

## Performance Considerations

### Connection Pooling Strategy
- Use thread-local connections via DuckDB's `cursor()` method
- Main connection in read-only mode for safety
- No traditional connection pool needed due to DuckDB's architecture

### Concurrent Request Handling
```python
# FastAPI naturally handles concurrent requests
# Each request gets its own thread-local DuckDB connection

@app.on_event("startup")
async def startup_event():
    # Initialize main connection
    app.state.conn_manager = DuckDBConnectionManager(
        settings.database_path,
        read_only=settings.read_only
    )
    
    # Pre-discover macros for faster first requests
    app.state.macro_service = MacroIntrospectionService()
    await app.state.macro_service.cache_macros()
```

### Query Optimization
- Implement query timeouts using DuckDB's pragma settings
- Cache macro metadata to avoid repeated introspection queries
- Consider result streaming for large datasets
- Use pagination for table macros returning many rows

## Implementation Roadmap

### Phase 1: Core Functionality (Week 1)
1. Set up FastAPI project structure
2. Implement DuckDBConnectionManager with thread safety
3. Create MacroIntrospectionService for discovering macros
4. Build basic API endpoints for listing and executing macros

### Phase 2: Dynamic Endpoints (Week 2)
1. Implement MacroEndpointGenerator for dynamic route creation
2. Add parameter type validation and conversion
3. Handle both scalar and table macros appropriately
4. Create comprehensive error handling

### Phase 3: Production Features (Week 3)
1. Add health checks and monitoring endpoints
2. Implement structured logging with correlation IDs
3. Create Docker configuration and build pipeline
4. Add configuration management with environment variables

### Phase 4: Testing and Documentation (Week 4)
1. Write unit tests for all components
2. Create integration tests with test database
3. Generate OpenAPI documentation
4. Create deployment and operations guide

## Security Considerations

### Parameter Validation
```python
def validate_macro_parameters(params: Dict, macro_info: MacroInfo) -> Dict:
    """Validate and sanitize macro parameters"""
    validated = {}
    
    for param_name, param_type in zip(macro_info.parameters, macro_info.parameter_types):
        if param_name in params:
            # Type validation
            validated[param_name] = convert_to_duckdb_type(
                params[param_name], 
                param_type
            )
    
    return validated
```

### Query Safety
- Use parameterized queries exclusively
- Validate macro names against discovered macros only
- Implement request rate limiting per IP/API key
- Set maximum result size limits

## Monitoring and Observability

### Metrics to Track
```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter('duckdb_rest_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('duckdb_rest_request_duration_seconds', 'Request duration')

# Database metrics
active_connections = Gauge('duckdb_active_connections', 'Active database connections')
query_duration = Histogram('duckdb_query_duration_seconds', 'Query execution time', ['macro_name'])
```

### Structured Logging
```python
import structlog

logger = structlog.get_logger()

# Log macro execution
logger.info("macro_executed",
    macro_name=macro_name,
    parameters=params,
    duration_ms=duration,
    result_rows=row_count,
    request_id=request_id
)
```

This implementation plan provides a production-ready blueprint for building a RESTful server that exposes DuckDB macros as HTTP endpoints. The design prioritizes simplicity, performance, and operational excellence while leveraging DuckDB's powerful macro introspection capabilities and FastAPI's developer-friendly features.