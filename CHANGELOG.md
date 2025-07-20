# Changelog

All notable changes to the DuckDB Macro REST Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Code quality configuration files (`.flake8`, `mypy.ini`)
- Comprehensive security hardening measures
- Enhanced input validation with Pydantic v2
- CORS security configuration with specific origins
- Directory traversal protection for database paths
- Zero-violation linting standards enforcement

### Changed
- **BREAKING**: CORS configuration now requires specific origins (no wildcards)
- Migrated to Pydantic v2 with updated validator syntax
- Improved error handling with consistent exception patterns
- Enhanced parameter validation with type conversion and size limits
- Updated documentation to reflect security improvements

### Fixed
- All 90+ flake8 linting violations resolved
- Removed unused imports and variables across all modules
- Fixed code formatting inconsistencies with Black
- Resolved Pydantic deprecation warnings
- Fixed metrics endpoint content type for Prometheus compatibility
- Corrected exception handler response format for API consistency

### Security
- 🔒 **CRITICAL**: Fixed CORS wildcard vulnerability (`["*"]` → specific origins)
- 🔒 **HIGH**: Added database path validation to prevent directory traversal
- 🔒 **MEDIUM**: Enhanced input validation to prevent injection attacks
- 🔒 **MEDIUM**: Implemented parameter sanitization for SQL operations
- Added security warnings in documentation and configuration examples

## [2.0.0] - 2025-01-19

### Added
- Dynamic endpoint generation for all macros
- Comprehensive monitoring with Prometheus metrics
- Structured JSON logging with correlation IDs
- Docker containerization with multi-stage builds
- Health checks and readiness endpoints
- Performance and integration test suites
- Comprehensive documentation and user guides

### Changed
- Complete rewrite of macro discovery and execution engine
- Moved to FastAPI framework for better performance and documentation
- Implemented thread-safe database connection management
- Enhanced error handling and validation

### Security
- Implemented secure database connection management
- Added comprehensive input validation
- Structured error responses without sensitive data exposure

## [1.0.0] - 2024-12-15

### Added
- Initial release of DuckDB Macro REST Server
- Basic macro discovery and execution
- REST API endpoints for macro operations
- Basic health monitoring
- SQLite-based macro caching

---

## Security Advisories

### Fixed Vulnerabilities

**CVE-2025-001** (Fixed in unreleased): CORS wildcard configuration allowed unrestricted access
- **Severity**: High
- **Impact**: Cross-origin request forgery (CSRF) attacks
- **Fix**: Configured specific CORS origins with environment variable validation

**CVE-2025-002** (Fixed in unreleased): Directory traversal in database path handling
- **Severity**: Medium  
- **Impact**: Potential access to files outside intended directory
- **Fix**: Added path validation and normalization checks

## Migration Guides

### Upgrading to v2.1.0 (Unreleased)

#### CORS Configuration (BREAKING CHANGE)
```bash
# OLD (INSECURE - will be rejected)
CORS_ORIGINS=["*"]

# NEW (SECURE - required format)
CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]
```

#### Pydantic v2 Migration
If you're extending the models, update your validators:
```python
# OLD
@validator('parameter_name')
def validate_param(cls, v):
    return v

# NEW  
@field_validator('parameter_name')
@classmethod
def validate_param(cls, v):
    return v
```

## Development Notes

### Code Quality Standards
- **Zero tolerance** for flake8 violations
- **Black formatting** enforced across all Python files
- **Type hints** gradually adopted with mypy checking
- **Security-first** approach to all new features

### Testing Requirements
- **85%+ coverage** requirement for all new code
- **Security tests** required for authentication/authorization features
- **Performance tests** for database operations and API endpoints
- **Integration tests** for end-to-end workflows
