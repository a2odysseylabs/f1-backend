import os
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator
from pathlib import Path

class Settings(BaseSettings):
    # API Configuration
    PROJECT_NAME: str = "F1nsight Backend"
    API_V1_STR: str = "/api/v1"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8080",  # Vue dev server
        "http://localhost:4200",  # Angular dev server
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # FastF1 Cache Configuration
    FASTF1_CACHE_ENABLED: bool = True
    FASTF1_CACHE_DIR: str = str(Path.home() / ".cache" / "fastf1")
    
    # Data directories
    DATA_DIR: str = "data"
    CACHE_DIR: str = "cache"
    
    # Rate limiting
    REQUESTS_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 