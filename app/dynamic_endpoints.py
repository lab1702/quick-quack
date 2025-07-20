import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from app.database import get_connection_manager
from app.exceptions import MacroExecutionError, MacroParameterError
from app.macro_service import MacroIntrospectionService
from app.models import MacroExecutionResponse, MacroInfo, MacroType

logger = logging.getLogger(__name__)


class MacroEndpointGenerator:
    """Creates dynamic FastAPI endpoints for each discovered macro"""

    def __init__(self, macro_service: MacroIntrospectionService):
        self.macro_service = macro_service
        self.router = APIRouter()
        self._generated_endpoints: Dict[str, bool] = {}

    async def generate_all_endpoints(self):
        """Generate endpoints for all discovered macros"""
        macros = await self.macro_service.list_macros()

        for macro_info in macros:
            if macro_info.name not in self._generated_endpoints:
                self.create_endpoint(macro_info)
                self._generated_endpoints[macro_info.name] = True
                logger.info(f"Generated dynamic endpoint for macro: {macro_info.name}")

        logger.info(f"Generated {len(self._generated_endpoints)} dynamic endpoints")
        return self.router

    def create_endpoint(self, macro_info: MacroInfo):
        """Generate endpoint function for a specific macro"""

        if macro_info.macro_type == MacroType.TABLE:
            self._create_table_macro_endpoint(macro_info)
        else:
            self._create_scalar_macro_endpoint(macro_info)

    def _create_scalar_macro_endpoint(self, macro_info: MacroInfo):
        """Create endpoint for scalar macro"""

        async def scalar_endpoint(request: Request):
            """Execute scalar macro with query parameters"""
            try:
                # Extract query parameters
                params = dict(request.query_params)

                # Filter out empty parameters
                params = {k: v for k, v in params.items() if v and v.strip()}

                result = await self.macro_service.execute_macro(macro_info.name, params)

                return MacroExecutionResponse(
                    success=result["success"],
                    data=result["data"],
                    columns=result["columns"],
                    row_count=result["row_count"],
                    execution_time_ms=result["execution_time_ms"],
                )

            except MacroParameterError as e:
                raise HTTPException(status_code=400, detail=e.message)
            except MacroExecutionError as e:
                raise HTTPException(status_code=500, detail=e.message)
            except Exception as e:
                logger.error(f"Error executing scalar macro {macro_info.name}: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Execution failed: {str(e)}"
                )

        # Set function metadata
        scalar_endpoint.__name__ = f"execute_{macro_info.name}_scalar"

        # Add the endpoint to router
        self.router.add_api_route(
            path=f"/{macro_info.name}",
            endpoint=scalar_endpoint,
            methods=["GET"],
            response_model=MacroExecutionResponse,
            summary=f"Execute {macro_info.name} (scalar)",
            description=(
                f"Execute scalar macro {macro_info.name} with query parameters. "
                f"Parameters: {', '.join(macro_info.parameters)}"
            ),
        )

    def _create_table_macro_endpoint(self, macro_info: MacroInfo):
        """Create endpoints for table macro (both GET and POST)"""

        # GET endpoint with query parameters
        async def table_get_endpoint(request: Request):
            """Execute table macro with query parameters"""
            try:
                # Extract query parameters
                params = dict(request.query_params)

                # Filter out empty parameters
                params = {k: v for k, v in params.items() if v and v.strip()}

                result = await self.macro_service.execute_macro(macro_info.name, params)

                return MacroExecutionResponse(
                    success=result["success"],
                    data=result["data"],
                    columns=result["columns"],
                    row_count=result["row_count"],
                    execution_time_ms=result["execution_time_ms"],
                )

            except MacroParameterError as e:
                raise HTTPException(status_code=400, detail=e.message)
            except MacroExecutionError as e:
                raise HTTPException(status_code=500, detail=e.message)
            except Exception as e:
                logger.error(f"Error executing table macro {macro_info.name}: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Execution failed: {str(e)}"
                )

        # POST endpoint with JSON body
        async def table_post_endpoint(parameters: Dict[str, Any]):
            """Execute table macro with JSON parameters"""
            try:
                result = await self.macro_service.execute_macro(
                    macro_info.name, parameters
                )

                return MacroExecutionResponse(
                    success=result["success"],
                    data=result["data"],
                    columns=result["columns"],
                    row_count=result["row_count"],
                    execution_time_ms=result["execution_time_ms"],
                )

            except MacroParameterError as e:
                raise HTTPException(status_code=400, detail=e.message)
            except MacroExecutionError as e:
                raise HTTPException(status_code=500, detail=e.message)
            except Exception as e:
                logger.error(f"Error executing table macro {macro_info.name}: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Execution failed: {str(e)}"
                )

        # Set function metadata
        table_get_endpoint.__name__ = f"execute_{macro_info.name}_table_get"
        table_post_endpoint.__name__ = f"execute_{macro_info.name}_table_post"

        # Add GET endpoint
        self.router.add_api_route(
            path=f"/{macro_info.name}",
            endpoint=table_get_endpoint,
            methods=["GET"],
            response_model=MacroExecutionResponse,
            summary=f"Execute {macro_info.name} (table, GET)",
            description=(
                f"Execute table macro {macro_info.name} with query parameters. "
                f"Parameters: {', '.join(macro_info.parameters)}"
            ),
        )

        # Add POST endpoint
        self.router.add_api_route(
            path=f"/{macro_info.name}",
            endpoint=table_post_endpoint,
            methods=["POST"],
            response_model=MacroExecutionResponse,
            summary=f"Execute {macro_info.name} (table, POST)",
            description=f"Execute table macro {macro_info.name} with JSON body parameters",
        )


def get_macro_service_for_dynamic() -> MacroIntrospectionService:
    """Dependency to get macro service instance for dynamic endpoints"""
    connection_manager = get_connection_manager()
    return MacroIntrospectionService(connection_manager)
