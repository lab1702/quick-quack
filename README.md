# DuckDB Macro REST Server

A production-ready REST API server that exposes DuckDB macros as HTTP endpoints, featuring automatic discovery, dynamic routing, comprehensive monitoring, and enterprise-grade observability.

[![Tests](https://img.shields.io/badge/tests-passing-green)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-85%25-green)](htmlcov/)
[![Code Quality](https://img.shields.io/badge/flake8-0%20violations-green)](app/)
[![Security](https://img.shields.io/badge/security-hardened-green)](docs/DEVELOPMENT.md#security-standards)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![DuckDB](https://img.shields.io/badge/duckdb-1.3.2+-blue)](https://duckdb.org)
[![FastAPI](https://img.shields.io/badge/fastapi-0.104+-blue)](https://fastapi.tiangolo.com)

## 🚀 Quick Start

```bash
# 1. Setup
git clone <repository-url> && cd quick-quack
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Create sample database and start server
python create_test_db.py
uvicorn app.main:app --reload

# 3. Try it out
curl -X POST "http://localhost:8000/api/v1/macros/greet/execute" \
  -H "Content-Type: application/json" -d '{"name": "World"}'
```

**🔗 Quick Links:**
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health 
- **[Complete User Guide →](docs/USER_GUIDE.md)**
- **[Development Setup →](docs/DEVELOPMENT.md)**
- **[API Reference →](docs/API.md)**

## 🏗️ Key Features

### **🔄 Automatic Discovery**
- Auto-discovers all macros in your DuckDB database
- Supports scalar and table-valued macros with parameter inference
- Real-time cache updates and validation

### **🎯 Dynamic API**
- REST endpoints auto-generated for each macro
- GET (query params) and POST (JSON) support
- Comprehensive parameter validation and error handling

### **� Security Hardened**
- Input validation with Pydantic v2 and regex patterns
- CORS configuration with specific origins (no wildcards)
- Directory traversal protection for database paths
- SQL injection prevention and parameter sanitization

### **�📊 Production Ready**
- Health checks (`/health`, `/ready`) and Prometheus metrics (`/metrics`)
- Structured JSON logging with correlation IDs
- Zero linting violations (flake8) with enforced code quality
- Docker containerization with monitoring stack

### **🔍 Enterprise Observability**
- System resource monitoring (CPU, memory, disk)
- Database connection pool monitoring
- Request/response tracking and performance metrics
## 📚 Documentation

- **[📖 User Guide](docs/USER_GUIDE.md)** - Installation, configuration, and usage
- **[🔧 Development Guide](docs/DEVELOPMENT.md)** - Contributing and development setup  
- **[📋 API Reference](docs/API.md)** - Complete endpoint documentation
- **[🔒 Security Guide](docs/SECURITY.md)** - Security features and best practices

## 🧪 Testing & Quality

```bash
# Run all tests with coverage
pip install -r requirements-dev.txt
pytest tests/ --cov=app --cov-report=html

# Run specific test categories  
pytest tests/ -m "unit"          # Unit tests
pytest tests/ -m "integration"   # Integration tests
pytest tests/ -m "performance"   # Performance tests

# Code quality checks
black app tests                  # Format code
isort app tests                  # Sort imports  
flake8 app tests                 # Linting (0 violations)
mypy app                         # Type checking
```

**Quality Metrics**: 
- **Test Coverage**: 85%+ across all components
- **Test Suite**: 86 tests across unit, integration, and performance categories  
- **Code Quality**: Zero flake8 violations, Black formatted, type-checked
- **Security**: Hardened with input validation and CORS protection

## 🐳 Deployment

### Docker (Recommended)
```bash
# Quick start with Docker
docker build -t duckdb-macro-server .
docker run -p 8000:8000 -v /path/to/db:/app/data duckdb-macro-server

# Production with monitoring stack
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Configuration
```bash
# Copy and edit configuration
cp .env.example .env

# Key settings
DATABASE_PATH=./data/macros.db    # DuckDB database path
LOG_LEVEL=INFO                    # Logging level  
HOST=0.0.0.0                      # Server host
PORT=8000                         # Server port
```

See **[User Guide](docs/USER_GUIDE.md)** for detailed deployment options and **[Development Guide](docs/DEVELOPMENT.md)** for local setup.
## 🤝 Contributing

1. Fork the repository and create a feature branch
2. Follow the **[Development Guide](docs/DEVELOPMENT.md)** for setup
3. Add tests for new features and ensure all tests pass
4. Submit a pull request with a clear description

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🗺️ Roadmap

**Upcoming Features**: Authentication & authorization, Redis caching, GraphQL support, WebSocket streaming, multi-database support, distributed tracing

---

**Built with ❤️ using FastAPI, DuckDB, and Python**
