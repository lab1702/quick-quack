import logging
from typing import Any, Dict, List, Optional

from app.database import DuckDBConnectionManager
from app.exceptions import (
    MacroExecutionError,
    MacroNotFoundException,
    MacroParameterError,
)
from app.models import MacroInfo, MacroType

logger = logging.getLogger(__name__)


class MacroIntrospectionService:
    """Service for discovering and analyzing DuckDB macros"""

    def __init__(self, connection_manager: DuckDBConnectionManager):
        self.connection_manager = connection_manager
        self._macro_cache: Optional[Dict[str, MacroInfo]] = None

    async def list_macros(self) -> List[MacroInfo]:
        """
        Query duckdb_functions() to find all macros

        Returns:
            List of MacroInfo objects for all available macros
        """
        try:
            with self.connection_manager.get_connection_context() as conn:
                query = """
                SELECT
                    function_name,
                    parameters,
                    parameter_types,
                    return_type,
                    macro_definition,
                    function_type
                FROM duckdb_functions()
                WHERE function_type IN ('macro', 'table_macro')
                  AND internal = false
                ORDER BY function_name
                """

                result = conn.execute(query).fetchall()
                macros = [self._parse_macro(row) for row in result]

                # Update cache
                self._macro_cache = {macro.name: macro for macro in macros}

                logger.info(f"Discovered {len(macros)} macros")
                return macros

        except Exception as e:
            logger.error(f"Failed to list macros: {e}")
            raise

    def _parse_macro(self, row) -> MacroInfo:
        """
        Parse macro metadata into structured format

        Args:
            row: Result row from duckdb_functions() query

        Returns:
            MacroInfo object with parsed metadata
        """
        function_name = row[0]
        parameters = row[1] if row[1] else []
        parameter_types = row[2] if row[2] else []
        return_type = row[3] if row[3] else "UNKNOWN"
        macro_definition = row[4] if row[4] else ""
        function_type = row[5] if len(row) > 5 else "macro"

        # Handle None values in parameter_types by converting to empty strings
        if parameter_types:
            parameter_types = [
                pt if pt is not None else "UNKNOWN" for pt in parameter_types
            ]
        else:
            parameter_types = []

        # Determine macro type based on DuckDB function type
        if function_type == "table_macro":
            macro_type = MacroType.TABLE
        else:
            # Fallback to definition-based detection for regular macros
            is_table_macro = (
                "TABLE" in macro_definition.upper()
                or return_type.upper().startswith("TABLE")
                or "SELECT" in macro_definition.upper()
            )
            macro_type = MacroType.TABLE if is_table_macro else MacroType.SCALAR

        return MacroInfo(
            name=function_name,
            parameters=parameters,
            parameter_types=parameter_types,
            return_type=return_type,
            macro_type=macro_type,
        )

    async def get_macro_info(self, macro_name: str) -> Optional[MacroInfo]:
        """
        Get information about a specific macro

        Args:
            macro_name: Name of the macro to look up

        Returns:
            MacroInfo object if found, None otherwise
        """
        # Check cache first
        if self._macro_cache and macro_name in self._macro_cache:
            return self._macro_cache[macro_name]

        # If not cached, refresh the cache
        await self.list_macros()

        return self._macro_cache.get(macro_name) if self._macro_cache else None

    async def cache_macros(self):
        """Pre-load and cache all macro information"""
        await self.list_macros()
        logger.info("Macro cache initialized")

    def validate_macro_parameters(
        self, macro_info: MacroInfo, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate and convert macro parameters with enhanced validation

        Args:
            macro_info: Information about the macro
            params: Parameters to validate

        Returns:
            Validated and converted parameters

        Raises:
            ValueError: If parameters are invalid
        """
        validated = {}

        # Check if we have the right number of parameters
        expected_params = len(macro_info.parameters)
        provided_params = len([v for v in params.values() if v is not None])

        if provided_params > expected_params:
            raise MacroParameterError(
                f"Too many parameters. Expected {expected_params}, got {provided_params}"
            )

        # Validate each parameter
        for i, (param_name, param_type) in enumerate(
            zip(macro_info.parameters, macro_info.parameter_types)
        ):
            if param_name in params and params[param_name] is not None:
                try:
                    validated[param_name] = self._convert_parameter(
                        params[param_name], param_type
                    )
                except ValueError as e:
                    raise MacroParameterError(
                        f"Invalid value for parameter '{param_name}': {e}",
                        parameter_name=param_name,
                        expected_type=param_type,
                        provided_value=params[param_name],
                    )
            else:
                # Parameter not provided - check if it's required
                # For simplicity, we'll make all parameters optional for now
                # In a production system, you might want to mark required parameters
                pass

        # Validate parameter count matches what we're providing
        if len(validated) != provided_params:
            raise MacroParameterError(
                "Parameter validation failed: mismatch in parameter count"
            )

        return validated

    def _convert_parameter(self, value: Any, param_type: str) -> Any:
        """
        Convert parameter value to appropriate DuckDB type with enhanced validation

        Args:
            value: Parameter value to convert
            param_type: Expected DuckDB type

        Returns:
            Converted value

        Raises:
            ValueError: If conversion fails
        """
        if value is None:
            return None

        # Handle empty strings
        if isinstance(value, str) and value.strip() == "":
            return None

        param_type_upper = param_type.upper() if param_type else "UNKNOWN"

        try:
            # Integer types
            if param_type_upper in ["INTEGER", "BIGINT", "INT", "SMALLINT", "TINYINT"]:
                if isinstance(value, str):
                    # Handle string representations
                    value = value.strip()
                    if value.lower() in ["", "null", "none"]:
                        return None
                return int(float(value))  # Handle "1.0" -> 1

            # Floating point types
            elif param_type_upper in ["DOUBLE", "REAL", "FLOAT", "DECIMAL", "NUMERIC"]:
                if isinstance(value, str):
                    value = value.strip()
                    if value.lower() in ["", "null", "none"]:
                        return None
                return float(value)

            # String types
            elif param_type_upper in ["VARCHAR", "TEXT", "STRING", "CHAR"]:
                return str(value)

            # Boolean types
            elif param_type_upper == "BOOLEAN":
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    value_lower = value.lower().strip()
                    if value_lower in ["true", "1", "yes", "on", "t", "y"]:
                        return True
                    elif value_lower in ["false", "0", "no", "off", "f", "n"]:
                        return False
                    else:
                        raise ValueError(f"Cannot convert '{value}' to boolean")
                return bool(value)

            # Date/Time types - keep as strings for DuckDB to parse
            elif param_type_upper in ["DATE", "TIMESTAMP", "TIME"]:
                date_str = str(value).strip()
                if not date_str or date_str.lower() in ["null", "none"]:
                    return None
                # Basic validation for date format
                if param_type_upper == "DATE":
                    # Allow formats like YYYY-MM-DD, MM/DD/YYYY, etc.
                    import re

                    if not re.match(
                        r"\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}", date_str
                    ):
                        raise ValueError(
                            f"Invalid date format: {date_str}. Expected YYYY-MM-DD or MM/DD/YYYY"
                        )
                return date_str

            # JSON/Array types
            elif param_type_upper in ["JSON", "ARRAY"]:
                if isinstance(value, (dict, list)):
                    return value
                elif isinstance(value, str):
                    import json

                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        raise ValueError(f"Invalid JSON format: {value}")
                return value

            # Unknown or unsupported types - try automatic conversion for strings
            else:
                if param_type_upper == "UNKNOWN" and isinstance(value, str):
                    # Try to infer numeric type from string value
                    value_stripped = value.strip()

                    # Try integer conversion
                    if value_stripped.isdigit() or (
                        value_stripped.startswith("-") and value_stripped[1:].isdigit()
                    ):
                        try:
                            return int(value_stripped)
                        except ValueError:
                            pass

                    # Try float conversion
                    try:
                        # Check if it looks like a float
                        if "." in value_stripped or "e" in value_stripped.lower():
                            return float(value_stripped)
                        # Also try converting integer-looking strings to int
                        elif value_stripped.replace("-", "").isdigit():
                            return int(value_stripped)
                    except ValueError:
                        pass

                logger.warning(
                    f"Unknown parameter type {param_type}, passing value as-is"
                )
                return value

        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert '{value}' to {param_type}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error converting parameter: {e}")
            raise ValueError(f"Parameter conversion failed: {e}")

    async def execute_macro(
        self, macro_name: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a macro with given parameters

        Args:
            macro_name: Name of the macro to execute
            params: Parameters for the macro

        Returns:
            Execution results

        Raises:
            ValueError: If macro not found or parameters invalid
            RuntimeError: If execution fails
        """
        import time

        # Get macro information
        macro_info = await self.get_macro_info(macro_name)
        if not macro_info:
            # Get available macros for better error message
            available_macros = [m.name for m in await self.list_macros()]
            raise MacroNotFoundException(macro_name, available_macros)

        # Validate parameters
        try:
            validated_params = self.validate_macro_parameters(macro_info, params)
        except ValueError as e:
            raise MacroParameterError(str(e))

        try:
            with self.connection_manager.get_connection_context() as conn:
                start_time = time.time()

                # Build parameter list in the correct order
                param_values = []
                for param_name in macro_info.parameters:
                    if param_name in validated_params:
                        param_values.append(validated_params[param_name])

                # Execute macro based on type
                if macro_info.macro_type == MacroType.TABLE:
                    # For table macros, use SELECT * FROM macro(...)
                    if param_values:
                        placeholders = ",".join(["?" for _ in param_values])
                        query = f"SELECT * FROM {macro_name}({placeholders})"
                        result = conn.execute(query, param_values)
                    else:
                        query = f"SELECT * FROM {macro_name}()"
                        result = conn.execute(query)
                else:
                    # For scalar macros, use SELECT macro(...)
                    if param_values:
                        query = f"SELECT {macro_name}({','.join(['?' for _ in param_values])})"
                        result = conn.execute(query, param_values)
                    else:
                        query = f"SELECT {macro_name}()"
                        result = conn.execute(query)

                execution_time = (
                    time.time() - start_time
                ) * 1000  # Convert to milliseconds

                if macro_info.macro_type == MacroType.TABLE:
                    # For table macros, return all rows and column information
                    rows = result.fetchall()
                    columns = (
                        [desc[0] for desc in result.description]
                        if result.description
                        else []
                    )

                    return {
                        "success": True,
                        "data": rows,
                        "columns": columns,
                        "row_count": len(rows),
                        "execution_time_ms": execution_time,
                        "macro_type": macro_info.macro_type,
                    }
                else:
                    # For scalar macros, return single value
                    row = result.fetchone()
                    value = row[0] if row else None

                    return {
                        "success": True,
                        "data": value,
                        "columns": None,
                        "row_count": 1 if value is not None else 0,
                        "execution_time_ms": execution_time,
                        "macro_type": macro_info.macro_type,
                    }

        except Exception as e:
            logger.error(f"Failed to execute macro {macro_name}: {e}")
            if "does not exist" in str(e).lower():
                raise MacroNotFoundException(macro_name)
            else:
                raise MacroExecutionError(macro_name, str(e))
