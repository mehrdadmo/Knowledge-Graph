from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # PostgreSQL Configuration
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="logistics_kg", description="PostgreSQL database name")
    postgres_user: str = Field(default="postgres", description="PostgreSQL username")
    postgres_password: str = Field(default="password", description="PostgreSQL password")
    
    # Neo4j Configuration - Read from environment variables
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="password", description="Neo4j password")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    @property
    def postgres_dsn(self) -> str:
        # Check if we're in Cloud Run (Unix socket)
        if self.postgres_host.startswith("/cloudsql/"):
            dsn = f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            return dsn
        else:
            dsn = f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            return dsn
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Override defaults with environment variables
        extra = "ignore"


settings = Settings()
