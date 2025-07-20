from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class MacroType(str, Enum):
    """Types of DuckDB macros"""

    SCALAR = "scalar"
    TABLE = "table"


class MacroInfo(BaseModel):
    """Information about a DuckDB macro"""

    name: str = Field(
        ..., min_length=1, max_length=100, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$"
    )
    parameters: List[str]
    parameter_types: List[str]
    return_type: str
    macro_type: MacroType
    description: Optional[str] = None


class MacroExecutionRequest(BaseModel):
    """Request body for macro execution"""

    parameters: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, v):
        """Validate parameter values"""
        if len(v) > 50:
            raise ValueError("Too many parameters (max 50)")
        for key, value in v.items():
            if key.startswith("_") or key.startswith("$"):
                raise ValueError(f"Parameter name '{key}' is not allowed")
            if isinstance(value, str) and len(value) > 10000:
                raise ValueError(f"Parameter '{key}' value too long")
        return v


class MacroExecutionResponse(BaseModel):
    """Response from macro execution"""

    success: bool
    data: Optional[Any] = None
    columns: Optional[List[str]] = None
    row_count: Optional[int] = None
    execution_time_ms: Optional[float] = None


class ErrorResponse(BaseModel):
    """Structured error response"""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    database_connected: bool
    timestamp: str
    version: str
