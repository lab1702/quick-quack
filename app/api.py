import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.exceptions import MacroNotFoundException
from app.config import settings
from app.database import get_connection_manager
from app.macro_service import MacroIntrospectionService
from app.models import (
    HealthResponse,
    MacroExecutionRequest,
    MacroExecutionResponse,
    MacroInfo,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


def get_macro_service() -> MacroIntrospectionService:
    """Dependency to get macro service instance"""
    connection_manager = get_connection_manager()
    return MacroIntrospectionService(connection_manager)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Returns:
        HealthResponse with system status
    """
    try:
        connection_manager = get_connection_manager()
        db_connected = connection_manager.test_connection()

        return HealthResponse(
            status="healthy" if db_connected else "unhealthy",
            database_connected=db_connected,
            timestamp=datetime.utcnow().isoformat(),
            version=settings.version,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            database_connected=False,
            timestamp=datetime.utcnow().isoformat(),
            version=settings.version,
        )


@router.get("/macros", response_model=List[MacroInfo])
async def list_macros(
    macro_service: MacroIntrospectionService = Depends(get_macro_service),
):
    """
    List all available DuckDB macros

    Returns:
        List of MacroInfo objects describing available macros
    """
    try:
        macros = await macro_service.list_macros()
        logger.info(f"Listed {len(macros)} macros")
        return macros
    except Exception as e:
        logger.error(f"Failed to list macros: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve macros: {str(e)}"
        )


@router.get("/macros/{macro_name}", response_model=MacroInfo)
async def get_macro_info(
    macro_name: str,
    macro_service: MacroIntrospectionService = Depends(get_macro_service),
):
    """
    Get detailed information about a specific macro

    Args:
        macro_name: Name of the macro to retrieve

    Returns:
        MacroInfo object with detailed macro information
    """
    try:
        macro_info = await macro_service.get_macro_info(macro_name)
        if not macro_info:
            raise MacroNotFoundException(macro_name)

        logger.info(f"Retrieved info for macro: {macro_name}")
        return macro_info
    except MacroNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to get macro info for {macro_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve macro information: {str(e)}"
        )


@router.post("/macros/{macro_name}/execute", response_model=MacroExecutionResponse)
async def execute_macro(
    macro_name: str,
    request: MacroExecutionRequest,
    macro_service: MacroIntrospectionService = Depends(get_macro_service),
):
    """
    Execute a DuckDB macro with provided parameters

    Args:
        macro_name: Name of the macro to execute
        request: Request body containing macro parameters

    Returns:
        MacroExecutionResponse with execution results
    """
    try:
        result = await macro_service.execute_macro(macro_name, request.parameters)

        response = MacroExecutionResponse(
            success=result["success"],
            data=result["data"],
            columns=result["columns"],
            row_count=result["row_count"],
            execution_time_ms=result["execution_time_ms"],
        )

        logger.info(
            f"Executed macro {macro_name} successfully in {result['execution_time_ms']:.2f}ms"
        )
        return response

    except ValueError as e:
        # Parameter validation errors
        logger.warning(f"Parameter validation failed for macro {macro_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # Execution errors
        logger.error(f"Execution failed for macro {macro_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error executing macro {macro_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
