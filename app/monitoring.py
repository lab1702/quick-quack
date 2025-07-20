"""
Health check and monitoring endpoints for production deployment
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

import psutil
from fastapi import APIRouter
from pydantic import BaseModel

from app.database import get_connection_manager
from app.macro_service import MacroIntrospectionService

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthStatus(BaseModel):
    """Health check response model"""

    status: str
    timestamp: datetime
    uptime_seconds: float
    database_connected: bool
    macro_count: Optional[int] = None
    version: str = "1.0.0"


class DetailedHealthStatus(BaseModel):
    """Detailed health check with system metrics"""

    status: str
    timestamp: datetime
    uptime_seconds: float
    database_connected: bool
    macro_count: Optional[int] = None
    version: str = "1.0.0"
    system_metrics: Dict[str, Any]
    connection_pool_status: Dict[str, Any]


class ReadinessStatus(BaseModel):
    """Readiness check response model"""

    ready: bool
    timestamp: datetime
    checks: Dict[str, bool]
    details: Dict[str, Any]


# Track application start time
_start_time = time.time()


def get_uptime() -> float:
    """Get application uptime in seconds"""
    return time.time() - _start_time


def get_system_metrics() -> Dict[str, Any]:
    """Get system performance metrics"""
    try:
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.1)
        disk = psutil.disk_usage("/")

        return {
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": memory.percent,
            },
            "cpu": {"usage_percent": cpu, "core_count": psutil.cpu_count()},
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_percent": round((disk.used / disk.total) * 100, 2),
            },
        }
    except Exception as e:
        logger.warning(f"Failed to get system metrics: {e}")
        return {"error": "Failed to retrieve system metrics"}


async def check_database_health(connection_manager) -> tuple[bool, Dict[str, Any]]:
    """Check database connectivity and get connection stats"""
    try:
        # Test database connection
        with connection_manager.get_connection_context() as conn:
            result = conn.execute("SELECT 1 as test").fetchone()
            if result and result[0] == 1:
                connection_stats = {
                    "active_connections": connection_manager.get_active_connection_count(),
                    "max_connections": connection_manager.max_connections,
                    "connection_pool_healthy": True,
                }
                return True, connection_stats
            else:
                return False, {"error": "Database query failed"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False, {"error": str(e)}


async def check_macro_service(
    macro_service: MacroIntrospectionService,
) -> tuple[bool, int]:
    """Check macro service and get macro count"""
    try:
        macros = await macro_service.list_macros()
        return True, len(macros)
    except Exception as e:
        logger.error(f"Macro service health check failed: {e}")
        return False, 0


@router.get("/health", response_model=HealthStatus, tags=["Health"])
async def health_check():
    """
    Basic health check endpoint for load balancers and monitoring systems.
    Returns simple status information.
    """
    connection_manager = get_connection_manager()

    # Quick database connectivity check
    db_healthy, _ = await check_database_health(connection_manager)

    # Quick macro count check
    try:
        macro_service = MacroIntrospectionService(connection_manager)
        macro_healthy, macro_count = await check_macro_service(macro_service)
    except Exception:
        macro_healthy, macro_count = False, None

    status = "healthy" if db_healthy and macro_healthy else "unhealthy"

    return HealthStatus(
        status=status,
        timestamp=datetime.utcnow(),
        uptime_seconds=get_uptime(),
        database_connected=db_healthy,
        macro_count=macro_count if macro_healthy else None,
    )


@router.get("/health/detailed", response_model=DetailedHealthStatus, tags=["Health"])
async def detailed_health_check():
    """
    Detailed health check with system metrics and connection pool status.
    Use for monitoring dashboards and detailed diagnostics.
    """
    connection_manager = get_connection_manager()

    # Database health check
    db_healthy, connection_stats = await check_database_health(connection_manager)

    # Macro service health check
    try:
        macro_service = MacroIntrospectionService(connection_manager)
        macro_healthy, macro_count = await check_macro_service(macro_service)
    except Exception:
        macro_healthy, macro_count = False, None

    # System metrics
    system_metrics = get_system_metrics()

    status = "healthy" if db_healthy and macro_healthy else "unhealthy"

    return DetailedHealthStatus(
        status=status,
        timestamp=datetime.utcnow(),
        uptime_seconds=get_uptime(),
        database_connected=db_healthy,
        macro_count=macro_count if macro_healthy else None,
        system_metrics=system_metrics,
        connection_pool_status=connection_stats,
    )


@router.get("/ready", response_model=ReadinessStatus, tags=["Health"])
async def readiness_check():
    """
    Kubernetes-style readiness check.
    Returns detailed status of all critical components.
    """
    connection_manager = get_connection_manager()
    checks = {}
    details = {}

    # Database readiness
    db_healthy, db_details = await check_database_health(connection_manager)
    checks["database"] = db_healthy
    details["database"] = db_details

    # Macro service readiness
    try:
        macro_service = MacroIntrospectionService(connection_manager)
        macro_healthy, macro_count = await check_macro_service(macro_service)
        checks["macro_service"] = macro_healthy
        details["macro_service"] = {"macro_count": macro_count}
    except Exception as e:
        checks["macro_service"] = False
        details["macro_service"] = {"error": str(e)}

    # System resource checks
    system_metrics = get_system_metrics()
    memory_ok = True
    disk_ok = True

    if "memory" in system_metrics:
        memory_ok = system_metrics["memory"]["used_percent"] < 90
    if "disk" in system_metrics:
        disk_ok = system_metrics["disk"]["used_percent"] < 95

    checks["memory"] = memory_ok
    checks["disk"] = disk_ok
    details["system_metrics"] = system_metrics

    # Overall readiness
    ready = all(checks.values())

    return ReadinessStatus(
        ready=ready, timestamp=datetime.utcnow(), checks=checks, details=details
    )


@router.get("/metrics", tags=["Monitoring"])
async def prometheus_metrics():
    """
    Prometheus-compatible metrics endpoint.
    Returns metrics in Prometheus format.
    """
    from fastapi import Response

    connection_manager = get_connection_manager()

    # Get basic metrics
    uptime = get_uptime()
    db_healthy, connection_stats = await check_database_health(connection_manager)

    try:
        macro_service = MacroIntrospectionService(connection_manager)
        _, macro_count = await check_macro_service(macro_service)
    except Exception:
        macro_count = 0

    # System metrics
    system_metrics = get_system_metrics()

    # Format as Prometheus metrics
    metrics = [
        "# HELP duckdb_rest_uptime_seconds Application uptime in seconds",
        "# TYPE duckdb_rest_uptime_seconds gauge",
        f"duckdb_rest_uptime_seconds {uptime}",
        "",
        "# HELP duckdb_rest_database_connected Database connection status "
        "(1=connected, 0=disconnected)",
        "# TYPE duckdb_rest_database_connected gauge",
        f"duckdb_rest_database_connected {1 if db_healthy else 0}",
        "",
        "# HELP duckdb_rest_macro_count Number of discovered macros",
        "# TYPE duckdb_rest_macro_count gauge",
        f"duckdb_rest_macro_count {macro_count}",
        "",
    ]

    if "connection_pool_healthy" in connection_stats:
        metrics.extend(
            [
                "# HELP duckdb_rest_active_connections Current active database connections",
                "# TYPE duckdb_rest_active_connections gauge",
                f"duckdb_rest_active_connections {connection_stats.get('active_connections', 0)}",
                "",
            ]
        )

    if "memory" in system_metrics:
        memory = system_metrics["memory"]
        metrics.extend(
            [
                "# HELP duckdb_rest_memory_usage_percent Memory usage percentage",
                "# TYPE duckdb_rest_memory_usage_percent gauge",
                f"duckdb_rest_memory_usage_percent {memory['used_percent']}",
                "",
            ]
        )

    if "cpu" in system_metrics:
        cpu = system_metrics["cpu"]
        metrics.extend(
            [
                "# HELP duckdb_rest_cpu_usage_percent CPU usage percentage",
                "# TYPE duckdb_rest_cpu_usage_percent gauge",
                f"duckdb_rest_cpu_usage_percent {cpu['usage_percent']}",
                "",
            ]
        )

    return Response(content="\n".join(metrics), media_type="text/plain; charset=utf-8")
