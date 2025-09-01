"""Application settings and configuration"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator, Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = Field(default="FlowMastery Platform", description="Application name")
    APP_VERSION: str = Field(default="2.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    # Server
    BACKEND_HOST: str = Field(default="0.0.0.0", description="Backend host")
    BACKEND_PORT: int = Field(default=8000, description="Backend port")
    FRONTEND_PORT: int = Field(default=3000, description="Frontend port")
    
    # Security
    SECRET_KEY: str = Field(..., description="Cryptographic secret key for JWT and encryption")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration in days")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ENCRYPTION_KEY: str = Field(..., description="Encryption key for sensitive data")
    
    # Trusted Hosts (Host Header Protection)
    ALLOWED_HOSTS: str = Field(
        default="localhost,127.0.0.1,0.0.0.0", 
        description="Comma-separated list of allowed hosts"
    )
    
    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:5176,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:5176,http://localhost:8000,http://127.0.0.1:8000",
        description="Comma-separated list of CORS origins"
    )
    
    # CORS Security Configuration
    CORS_ALLOW_METHODS: str = Field(
        default="GET,POST,PUT,DELETE,OPTIONS,PATCH",
        description="Comma-separated list of allowed HTTP methods"
    )
    CORS_ALLOW_HEADERS: str = Field(
        default="Content-Type,Authorization,Accept,Origin,User-Agent,Cache-Control,X-Requested-With,ngrok-skip-browser-warning",
        description="Comma-separated list of allowed headers"
    )
    
    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL database URL")
    DB_ECHO: bool = Field(default=False, description="Enable SQLAlchemy query logging")
    DB_SSL_MODE: Optional[str] = Field(default=None, description="Database SSL mode")
    
    # Database connection components (required for Docker)
    POSTGRES_DB: str = Field(default="metrics_dashboard", description="PostgreSQL database name")
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(..., description="PostgreSQL password")
    
    # Email
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP server host")
    SMTP_PORT: int = Field(default=587, description="SMTP server port")
    SMTP_USERNAME: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")
    SMTP_USE_TLS: bool = Field(default=True, description="Use TLS for SMTP")
    FROM_EMAIL: str = Field(default="noreply@flowmastery.com", description="Default from email address")
    
    # Frontend URL for invitation links
    FRONTEND_URL: str = Field(default="http://localhost:3000", description="Frontend application URL")
    
    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379/0", description="Redis connection URL")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    CACHE_TTL: int = Field(default=300, description="Cache TTL in seconds")
    
    # n8n Integration
    N8N_API_URL: Optional[str] = Field(default=None, description="n8n API URL")
    N8N_API_KEY: Optional[str] = Field(default=None, description="n8n API key")
    N8N_BASE_URL: Optional[str] = Field(default=None, description="n8n base URL")
    
    # AI Services
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format")
    
    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, description="Enable metrics collection")
    METRICS_PORT: int = Field(default=9090, description="Metrics server port")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Rate limit per minute")
    
    # Environment
    ENVIRONMENT: str = Field(default="development", description="Application environment")
    
    # Invitation Token Security
    INVITATION_TOKEN_EXPIRE_HOURS: int = Field(default=48, description="Invitation token expiration in hours")
    
    # Frontend URLs (for Docker)
    REACT_APP_API_URL: Optional[str] = Field(default=None, description="React app API URL")
    VITE_API_URL: Optional[str] = Field(default=None, description="Vite API URL")
    
    def get_cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    def get_allowed_hosts_list(self) -> List[str]:
        """Get allowed hosts as a list"""
        if isinstance(self.ALLOWED_HOSTS, str):
            hosts = [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]
            # Add wildcard for development if DEBUG is True
            if self.DEBUG and "*" not in hosts:
                hosts.append("*")
            return hosts
        return self.ALLOWED_HOSTS
    
    def get_cors_methods_list(self) -> List[str]:
        """Get CORS allowed methods as a list"""
        if isinstance(self.CORS_ALLOW_METHODS, str):
            methods = [method.strip().upper() for method in self.CORS_ALLOW_METHODS.split(",") if method.strip()]
            # Ensure OPTIONS is always included for preflight requests
            if "OPTIONS" not in methods:
                methods.append("OPTIONS")
            return methods
        return self.CORS_ALLOW_METHODS
    
    def get_cors_headers_list(self) -> List[str]:
        """Get CORS allowed headers as a list"""
        if isinstance(self.CORS_ALLOW_HEADERS, str):
            headers = [header.strip() for header in self.CORS_ALLOW_HEADERS.split(",") if header.strip()]
            # Ensure essential headers are always included
            essential_headers = ["Content-Type", "Authorization", "Accept", "Origin"]
            for header in essential_headers:
                if header not in [h.lower() for h in headers] and header.lower() not in [h.lower() for h in headers]:
                    headers.append(header)
            return headers
        return self.CORS_ALLOW_HEADERS
    
    def get_database_url(self) -> str:
        """Get database URL, preferring environment-specific construction for Docker"""
        # If running in Docker with separate env vars, construct URL
        if (self.POSTGRES_USER and self.POSTGRES_PASSWORD and self.POSTGRES_DB and 
            "postgres:5432" in self.DATABASE_URL):
            return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@postgres:5432/{self.POSTGRES_DB}"
        return self.DATABASE_URL
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()