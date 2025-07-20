"""
Custom exceptions for the DuckDB Macro REST Server
"""

from typing import Any, Dict, Optional


class MacroRestException(Exception):
    """Base exception for DuckDB Macro REST Server"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class MacroNotFoundException(MacroRestException):
    """Raised when a requested macro is not found"""

    def __init__(self, macro_name: str, available_macros: Optional[list] = None):
        details = {"macro_name": macro_name}
        if available_macros:
            details["available_macros"] = available_macros[:10]  # Limit to first 10

        super().__init__(f"Macro '{macro_name}' not found", details)


class MacroParameterError(MacroRestException):
    """Raised when macro parameters are invalid"""

    def __init__(
        self,
        message: str,
        parameter_name: Optional[str] = None,
        expected_type: Optional[str] = None,
        provided_value: Optional[Any] = None,
    ):
        details = {}
        if parameter_name:
            details["parameter_name"] = parameter_name
        if expected_type:
            details["expected_type"] = expected_type
        if provided_value is not None:
            details["provided_value"] = str(provided_value)

        super().__init__(message, details)


class MacroExecutionError(MacroRestException):
    """Raised when macro execution fails"""

    def __init__(
        self, macro_name: str, original_error: str, query: Optional[str] = None
    ):
        details = {"macro_name": macro_name, "original_error": original_error}
        if query:
            details["query"] = query

        super().__init__(
            f"Failed to execute macro '{macro_name}': {original_error}", details
        )


class DatabaseConnectionError(MacroRestException):
    """Raised when database connection fails"""

    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message, {"component": "database"})


class MacroTypeError(MacroRestException):
    """Raised when there's an issue with macro type detection or handling"""

    def __init__(
        self, macro_name: str, detected_type: str, expected_type: Optional[str] = None
    ):
        details = {"macro_name": macro_name, "detected_type": detected_type}
        if expected_type:
            details["expected_type"] = expected_type

        message = f"Macro type error for '{macro_name}': detected as {detected_type}"
        if expected_type:
            message += f", expected {expected_type}"

        super().__init__(message, details)


class ConfigurationError(MacroRestException):
    """Raised when there's a configuration issue"""

    def __init__(self, setting_name: str, message: str):
        details = {"setting_name": setting_name}
        super().__init__(
            f"Configuration error for '{setting_name}': {message}", details
        )
