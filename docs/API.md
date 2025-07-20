# API Documentation

## Overview

The DuckDB Macro REST Server provides a RESTful API for discovering and executing DuckDB macros. This document describes all available endpoints, request/response formats, and usage examples.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. This may be added in future versions.

## Content Types

- All POST requests should use `Content-Type: application/json`
- All responses return `Content-Type: application/json` unless otherwise specified
- Metrics endpoint returns `Content-Type: text/plain; charset=utf-8`

## Endpoints

### Health and Monitoring

#### GET /health

Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:30:00.123456",
  "uptime_seconds": 3600.5,
  "database_connected": true,
  "macro_count": 7,
  "version": "1.0.0"
}
```

**Status Codes:**
- `200`: Service is healthy
- `503`: Service is unhealthy

#### GET /health/detailed

Detailed health check with system metrics.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:30:00.123456",
  "uptime_seconds": 3600.5,
  "database_connected": true,
  "macro_count": 7,
  "version": "1.0.0",
  "system_metrics": {
    "memory": {
      "total_gb": 16.0,
      "available_gb": 12.5,
      "used_percent": 22.0
    },
    "cpu": {
      "usage_percent": 15.5,
      "core_count": 8
    },
    "disk": {
      "total_gb": 500.0,
      "free_gb": 250.0,
      "used_percent": 50.0
    }
  },
  "connection_pool_status": {
    "active_connections": 3,
    "max_connections": 10,
    "connection_pool_healthy": true
  }
}
```

#### GET /ready

Kubernetes-style readiness check.

**Response:**
```json
{
  "ready": true,
  "timestamp": "2024-01-20T10:30:00.123456",
  "checks": {
    "database": true,
    "macro_service": true,
    "memory": true,
    "disk": true
  },
  "details": {
    "database": {
      "active_connections": 3,
      "max_connections": 10,
      "connection_pool_healthy": true
    },
    "macro_service": {
      "macro_count": 7
    },
    "system_metrics": {
      "memory": {
        "total_gb": 16.0,
        "available_gb": 12.5,
        "used_percent": 22.0
      },
      "cpu": {
        "usage_percent": 15.5,
        "core_count": 8
      },
      "disk": {
        "total_gb": 500.0,
        "free_gb": 250.0,
        "used_percent": 50.0
      }
    }
  }
}
```

**Status Codes:**
- `200`: Service is ready
- `503`: Service is not ready

#### GET /metrics

Prometheus-compatible metrics endpoint.

**Response:** (text/plain)
```
# HELP duckdb_rest_uptime_seconds Application uptime in seconds
# TYPE duckdb_rest_uptime_seconds gauge
duckdb_rest_uptime_seconds 3600.5

# HELP duckdb_rest_database_connected Database connection status (1=connected, 0=disconnected)
# TYPE duckdb_rest_database_connected gauge
duckdb_rest_database_connected 1

# HELP duckdb_rest_macro_count Number of discovered macros
# TYPE duckdb_rest_macro_count gauge
duckdb_rest_macro_count 7

# HELP duckdb_rest_active_connections Current active database connections
# TYPE duckdb_rest_active_connections gauge
duckdb_rest_active_connections 3

# HELP duckdb_rest_memory_usage_percent Memory usage percentage
# TYPE duckdb_rest_memory_usage_percent gauge
duckdb_rest_memory_usage_percent 22.0

# HELP duckdb_rest_cpu_usage_percent CPU usage percentage
# TYPE duckdb_rest_cpu_usage_percent gauge
duckdb_rest_cpu_usage_percent 15.5

# HELP duckdb_rest_disk_usage_percent Disk usage percentage
# TYPE duckdb_rest_disk_usage_percent gauge
duckdb_rest_disk_usage_percent 50.0
```

### Macro Discovery

#### GET /api/v1/macros

List all available macros.

**Response:**
```json
[
  {
    "name": "greet",
    "parameters": ["name"],
    "parameter_types": ["VARCHAR"],
    "return_type": "TABLE",
    "macro_type": "table"
  },
  {
    "name": "employees_by_department",
    "parameters": ["dept"],
    "parameter_types": ["VARCHAR"],
    "return_type": "TABLE",
    "macro_type": "table"
  }
]
```

#### GET /api/v1/macros/{macro_name}

Get information about a specific macro.

**Parameters:**
- `macro_name` (path): Name of the macro

**Response:**
```json
{
  "name": "greet",
  "parameters": ["name"],
  "parameter_types": ["VARCHAR"],
  "return_type": "TABLE",
  "macro_type": "table"
}
```

**Status Codes:**
- `200`: Macro found
- `404`: Macro not found

### Macro Execution

#### POST /api/v1/macros/{macro_name}/execute

Execute a macro with parameters.

**Parameters:**
- `macro_name` (path): Name of the macro to execute

**Request Body:**
```json
{
  "name": "World"
}
```

**Response:**
```json
[
  {
    "greeting": "Hello, World!"
  }
]
```

**Status Codes:**
- `200`: Execution successful
- `400`: Invalid parameters
- `404`: Macro not found
- `422`: Validation error
- `500`: Execution error

#### Examples

**Simple macro with no parameters:**
```bash
curl -X POST "http://localhost:8000/api/v1/macros/employee_count/execute" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Macro with string parameter:**
```bash
curl -X POST "http://localhost:8000/api/v1/macros/greet/execute" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}'
```

**Macro with numeric parameter:**
```bash
curl -X POST "http://localhost:8000/api/v1/macros/high_earners/execute" \
  -H "Content-Type: application/json" \
  -d '{"min_salary": 75000}'
```

### Dynamic Endpoints

Macros are also available as dynamic endpoints for convenience.

#### GET /{macro_name}

Execute a macro using query parameters (for simple cases).

**Example:**
```bash
curl "http://localhost:8000/greet?name=World"
```

#### POST /{macro_name}

Execute a macro using JSON body.

**Example:**
```bash
curl -X POST "http://localhost:8000/employees_by_department" \
  -H "Content-Type: application/json" \
  -d '{"dept": "Engineering"}'
```

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error description",
  "error_code": "MACRO_NOT_FOUND",
  "timestamp": "2024-01-20T10:30:00.123456"
}
```

### Common Error Codes

- `MACRO_NOT_FOUND`: The specified macro does not exist
- `INVALID_PARAMETERS`: The provided parameters are invalid
- `EXECUTION_ERROR`: An error occurred during macro execution
- `VALIDATION_ERROR`: Request validation failed

## Rate Limiting

Currently, no rate limiting is implemented. This may be added in future versions.

## Response Headers

All responses include these headers:

- `X-Request-ID`: Unique identifier for the request
- `X-Process-Time`: Time taken to process the request (in seconds)

## OpenAPI Specification

The complete OpenAPI specification is available at:
- JSON: `GET /openapi.json`
- Interactive docs: `GET /docs`
- ReDoc: `GET /redoc`

## Client Examples

### Python

```python
import requests

# List macros
response = requests.get("http://localhost:8000/api/v1/macros")
macros = response.json()

# Execute macro
response = requests.post(
    "http://localhost:8000/api/v1/macros/greet/execute",
    json={"name": "World"}
)
result = response.json()
print(result[0]["greeting"])  # "Hello, World!"
```

### JavaScript

```javascript
// List macros
fetch('http://localhost:8000/api/v1/macros')
  .then(response => response.json())
  .then(macros => console.log(macros));

// Execute macro
fetch('http://localhost:8000/api/v1/macros/greet/execute', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({name: 'World'})
})
  .then(response => response.json())
  .then(result => console.log(result[0].greeting));
```

### cURL

```bash
# Health check
curl http://localhost:8000/health

# List macros
curl http://localhost:8000/api/v1/macros

# Execute macro
curl -X POST http://localhost:8000/api/v1/macros/greet/execute \
  -H "Content-Type: application/json" \
  -d '{"name": "World"}'

# Using dynamic endpoint
curl "http://localhost:8000/greet?name=World"
```
