# Quick Quack User Guide

This guide provides detailed information for deploying and using Quick Quack in production.

## Installation

### Development
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker
```bash
docker build -t quick-quack .
docker run -p 8000:8000 -v ./data:/app/data quick-quack
```

### Production
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `data/macros.db` | Path to DuckDB database file (validated for security) |
| `READ_ONLY` | `true` | Whether to open database in read-only mode |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `HOST` | `0.0.0.0` | Host to bind the server |
| `PORT` | `8000` | Port to bind the server |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins - **NEVER use ["*"] in production** |
| `MAX_REQUEST_SIZE` | `1048576` | Maximum request size in bytes (1MB) |
| `RATE_LIMIT_REQUESTS` | `100` | Maximum requests per minute per IP |

⚠️ **Security Note**: Always specify exact CORS origins in production. Wildcard (`*`) origins are disabled for security.

### Example .env File

```bash
DATABASE_PATH=./data/production.duckdb
READ_ONLY=true
LOG_LEVEL=INFO  
HOST=0.0.0.0
PORT=8000
# Security: Specify exact domains, never use "*"
CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]
MAX_REQUEST_SIZE=2097152
RATE_LIMIT_REQUESTS=200
```

## Macro Management

DuckDB macros are user-defined functions automatically discovered by the server. Create them using standard DuckDB SQL syntax.

### Creating Macros

**Simple Macro:**
```sql
CREATE MACRO greet(name) AS 
SELECT 'Hello, ' || name || '!' as greeting;
```

**Table Macro:**
```sql
CREATE MACRO recent_sales(days) AS 
TABLE SELECT * FROM sales WHERE sale_date >= current_date - interval '${days}' day;
```

### Using Macros via API

**Execute macro:**
```bash
curl -X POST http://localhost:8000/macro/greet \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"name": "World"}}'
```

**List available macros:**
```bash
curl http://localhost:8000/macros
```

See [API Documentation](API.md) for complete endpoint details.

## Monitoring

### Health Checks
```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
```

### Metrics
```bash
curl http://localhost:8000/metrics
```

## Deployment

### Docker Compose (Recommended)
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes
See example manifests in the `k8s/` directory for production Kubernetes deployment.

## Troubleshooting

### Common Issues

1. **Database Connection Errors**: Check database path and permissions
2. **Macro Not Found**: Verify macros exist with `SELECT * FROM duckdb_functions() WHERE function_type = 'macro'`
3. **Parameter Validation**: Ensure parameter names and types match macro definition
4. **Performance Issues**: Check database query performance and system resources

### Debug Mode
```bash
export LOG_LEVEL=DEBUG
```

### Getting Help

For additional support:
- Check logs with debug logging enabled
- Verify configuration and environment variables
- Review [API Documentation](API.md) for endpoint details
- Consult [Development Guide](DEVELOPMENT.md) for troubleshooting
