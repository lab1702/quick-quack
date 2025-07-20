from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import router
from app.config import settings
from app.database import get_connection_manager
from app.dynamic_endpoints import MacroEndpointGenerator
from app.exceptions import (
    DatabaseConnectionError,
    MacroExecutionError,
    MacroNotFoundException,
    MacroParameterError,
    MacroRestException,
)
from app.logging_config import (
    CorrelationIdMiddleware,
    get_structured_logger,
    setup_structured_logging,
)
from app.macro_service import MacroIntrospectionService
from app.models import ErrorResponse
from app.monitoring import router as monitoring_router

# Configure structured logging
setup_structured_logging(
    service_name="duckdb-macro-rest",
    log_level=settings.log_level,
    enable_json_logging=getattr(settings, "json_logging", True),
)

# Get structured logger
logger = get_structured_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting DuckDB Macro REST Server")

    try:
        # Initialize connection manager
        connection_manager = get_connection_manager()

        # Test database connection
        if connection_manager.test_connection():
            logger.info("Database connection established successfully")
        else:
            logger.error("Failed to establish database connection")

        # Pre-cache macros for faster first requests
        macro_service = MacroIntrospectionService(connection_manager)
        await macro_service.cache_macros()

        # Generate dynamic endpoints for all macros
        endpoint_generator = MacroEndpointGenerator(macro_service)
        dynamic_router = await endpoint_generator.generate_all_endpoints()

        # Include dynamic router at a different path to avoid conflicts
        app.include_router(dynamic_router, prefix=f"{settings.api_prefix}/execute")

        logger.info("Application startup completed")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down DuckDB Macro REST Server")
    try:
        connection_manager = get_connection_manager()
        connection_manager.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.title,
    description=settings.description,
    version=settings.version,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.cors_origins
        if hasattr(settings, "cors_origins")
        else ["http://localhost:3000"]
    ),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Add correlation ID tracking middleware
app.add_middleware(CorrelationIdMiddleware)

# Include API router
app.include_router(router, prefix=settings.api_prefix)

# Include monitoring router (health checks, metrics, etc.)
app.include_router(monitoring_router, tags=["Monitoring"])


@app.exception_handler(MacroParameterError)
async def macro_parameter_error_handler(request: Request, exc: MacroParameterError):
    """Handle macro parameter validation errors"""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="parameter_error", message=exc.message, details=exc.details
        ).dict(),
    )


@app.exception_handler(MacroExecutionError)
async def macro_execution_error_handler(request: Request, exc: MacroExecutionError):
    """Handle macro execution errors"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="execution_error", message=exc.message, details=exc.details
        ).dict(),
    )


@app.exception_handler(DatabaseConnectionError)
async def database_connection_error_handler(
    request: Request, exc: DatabaseConnectionError
):
    """Handle database connection errors"""
    return JSONResponse(
        status_code=503,
        content=ErrorResponse(
            error="database_connection_error", message=exc.message, details=exc.details
        ).dict(),
    )


@app.exception_handler(MacroNotFoundException)
async def macro_not_found_handler(request: Request, exc: MacroNotFoundException):
    """Handle macro not found exceptions"""
    return JSONResponse(
        status_code=404,
        content={
            "detail": exc.message,
        },
    )


@app.exception_handler(MacroRestException)
async def macro_rest_exception_handler(request: Request, exc: MacroRestException):
    """Handle general macro REST exceptions"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="macro_rest_error", message=exc.message, details=exc.details
        ).dict(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error response"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="http_error",
            message=exc.detail,
            details={"status_code": exc.status_code},
        ).dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_error",
            message="An unexpected error occurred",
            details={"error_type": type(exc).__name__},
        ).dict(),
    )


@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "message": "DuckDB Macro REST Server",
        "version": settings.version,
        "docs": "/docs",
        "api": settings.api_prefix,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info",
    )
