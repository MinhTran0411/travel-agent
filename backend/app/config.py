from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name: str = os.getenv("DATABASE_NAME", "travel_agent")
    
    # JWT Settings
    jwks_url: str = os.getenv("JWKS_URL", "")  # URL to fetch public keys
    jwt_issuer: str = os.getenv("JWT_ISSUER", "")  # Expected token issuer

    # Service URLs
    orchestration_host: str = os.getenv("ORCHESTRATION_HOST", "http://host.docker.internal:8000")
    
    # Feature flags
    enable_enrichment: bool = True
    enable_scraping: bool = True
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings() 