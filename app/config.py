from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings"""

    # Database configuration
    database_path: str = "data/database.duckdb"
    read_only: bool = True

    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Performance settings
    connection_timeout: int = 30
    query_timeout: int = 300
    max_result_size: int = 10000

    # API settings
    api_prefix: str = "/api/v1"
    title: str = "DuckDB Macro REST Server"
    description: str = "RESTful server that exposes DuckDB macros as HTTP endpoints"
    version: str = "1.0.0"

    # Logging configuration
    log_level: str = "INFO"
    json_logging: bool = True

    # Security settings
    max_request_size: int = 1048576  # 1MB
    rate_limit_requests: int = 100  # requests per minute
    rate_limit_window: int = 60  # seconds

    # Production settings
    environment: str = "development"
    cors_origins: List[str] = ["http://localhost:3000"]

    class Config:
        env_prefix = "DUCKDB_REST_"
        env_file = ".env"


# Global settings instance
settings = Settings()
