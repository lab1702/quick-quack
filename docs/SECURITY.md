# Security Guide

## 🔒 Security Overview

The DuckDB Macro REST Server has been hardened with multiple security layers to ensure safe deployment in production environments. This document outlines our security measures and best practices.

## ✅ Implemented Security Features

### 1. CORS (Cross-Origin Resource Sharing) Protection

**Status**: ✅ SECURED

- **Default**: Specific origins only (`["http://localhost:3000"]` for development)
- **Production**: Must specify exact domains via `CORS_ORIGINS` environment variable
- **Blocked**: Wildcard (`["*"]`) origins are rejected with configuration warnings

```bash
# ✅ SECURE (Production)
CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]

# ❌ INSECURE (Blocked)  
CORS_ORIGINS=["*"]
```

### 2. Input Validation & Sanitization

**Status**: ✅ COMPREHENSIVE

- **Pydantic v2**: Strong type validation with regex patterns
- **Parameter Types**: Automatic type conversion with bounds checking
- **SQL Injection**: Parameter binding prevents injection attacks
- **Size Limits**: Request size limitations prevent DoS attacks

```python
# Example: Macro name validation
name: str = Field(
    ..., 
    min_length=1, 
    max_length=100, 
    pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$"
)
```

### 3. Database Security

**Status**: ✅ HARDENED

- **Path Validation**: Directory traversal protection
- **Read-Only Mode**: Default safe mode for production
- **Connection Limits**: Thread-safe connection pooling
- **Error Handling**: No sensitive data in error responses

```python
# Path validation prevents ../../../etc/passwd
def validate_database_path(path: str) -> str:
    normalized = os.path.normpath(path)
    if ".." in normalized or normalized.startswith("/"):
        raise ValueError("Invalid database path")
    return normalized
```

### 4. Error Handling & Information Disclosure

**Status**: ✅ SECURE

- **Structured Errors**: Consistent error format without stack traces
- **No Sensitive Data**: Database internals hidden from API responses
- **Correlation IDs**: Request tracking without exposing system details
- **Logging**: Security events logged without sensitive data

## 🛡️ Security Best Practices

### Production Deployment

#### 1. Environment Configuration
```bash
# Security-first configuration
DATABASE_PATH=./data/production.duckdb  # No absolute paths
READ_ONLY=true                          # Read-only mode
LOG_LEVEL=INFO                          # No debug info in production
CORS_ORIGINS=["https://yourdomain.com"] # Specific origins only
MAX_REQUEST_SIZE=1048576                # Limit request size
```

#### 2. Network Security
- Deploy behind reverse proxy (nginx/traefik)
- Use HTTPS/TLS encryption in production
- Implement rate limiting at proxy level
- Configure firewall rules for database access

#### 3. Container Security
```dockerfile
# Security-hardened container
FROM python:3.11-slim
RUN adduser --disabled-password --gecos '' appuser
USER appuser
WORKDIR /app
# ... rest of configuration
```

### 4. Monitoring & Alerting
- Monitor failed authentication attempts
- Alert on unusual request patterns  
- Track database connection errors
- Log security-relevant events

## 🔍 Security Testing

### Automated Security Checks

```bash
# Static security analysis
bandit -r app/ -f json -o security-report.json

# Dependency vulnerability scanning
safety check

# Container security scanning  
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image duckdb-macro-server:latest
```

### Manual Security Testing

#### 1. Input Validation Testing
```bash
# Test parameter injection
curl -X POST "http://localhost:8000/api/v1/macros/test/execute" \
  -H "Content-Type: application/json" \
  -d '{"param": "'; DROP TABLE users; --"}'

# Expected: 400 Bad Request with validation error
```

#### 2. Path Traversal Testing
```bash
# Test database path validation
curl -X GET "http://localhost:8000/health" \
  -H "X-Database-Path: ../../../etc/passwd"

# Expected: Rejected with validation error
```

#### 3. CORS Testing
```bash
# Test CORS policy
curl -X OPTIONS "http://localhost:8000/api/v1/macros" \
  -H "Origin: https://malicious-site.com" \
  -H "Access-Control-Request-Method: GET"

# Expected: CORS rejection for unauthorized origin
```

## 🚨 Security Incident Response

### 1. Immediate Response
- Isolate affected systems
- Review logs for breach indicators
- Disable compromised accounts/endpoints
- Document timeline and impact

### 2. Investigation
- Analyze attack vectors
- Review access logs and audit trails
- Identify data exposure scope
- Preserve evidence for analysis

### 3. Recovery
- Apply security patches
- Update credentials and certificates
- Enhance monitoring and alerting
- Conduct security review

## 📋 Security Checklist

### Pre-Deployment
- [ ] CORS origins configured (no wildcards)
- [ ] Database in read-only mode
- [ ] Input validation implemented
- [ ] Error handling prevents information disclosure
- [ ] Secrets not hardcoded in configuration
- [ ] Container runs as non-root user
- [ ] Dependencies scanned for vulnerabilities

### Post-Deployment
- [ ] Monitoring and alerting configured
- [ ] Security logs reviewed regularly
- [ ] Access controls implemented
- [ ] Backup and recovery tested
- [ ] Incident response plan documented
- [ ] Security training conducted

## 🔧 Security Configuration Reference

### Environment Variables
| Variable | Security Impact | Recommendation |
|----------|----------------|----------------|
| `CORS_ORIGINS` | **HIGH** | Never use `["*"]` in production |
| `DATABASE_PATH` | **MEDIUM** | Use relative paths only |
| `READ_ONLY` | **MEDIUM** | Always `true` in production |
| `LOG_LEVEL` | **LOW** | Use `INFO` or `WARNING` in production |
| `MAX_REQUEST_SIZE` | **MEDIUM** | Limit to prevent DoS attacks |

### Security Headers (Recommended)
Implement at reverse proxy level:
```nginx
# Security headers
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options DENY;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000";
add_header Content-Security-Policy "default-src 'self'";
```

## 📞 Security Contacts

For security issues, please contact:
- **Security Team**: security@yourdomain.com
- **Emergency**: Create GitHub security advisory
- **Non-urgent**: Open issue with `security` label

---

**Last Updated**: January 19, 2025  
**Security Review**: Completed  
**Next Review**: March 19, 2025
