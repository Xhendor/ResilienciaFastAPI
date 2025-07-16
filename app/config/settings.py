from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv
from typing import List
import json

# Cargar variables de entorno desde el archivo .env si existe
load_dotenv()

class Settings(BaseSettings):
    # Configuración de la aplicación
    APP_NAME: str = "API de Automóviles"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Configuración del servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "True").lower() in ("true", "1", "t")
    
    # Configuración de CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    
    # Configuración de API Keys
    API_KEYS: str = os.getenv("API_KEYS", "test-key")
    
    # Configuración de OpenTelemetry
    OTEL_ENABLED: bool = os.getenv("OTEL_ENABLED", "True").lower() in ("true", "1", "t")
    OTEL_SERVICE_NAME: str = os.getenv("OTEL_SERVICE_NAME", "automoviles-service")
    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    
    # Configuración de Circuit Breaker
    CIRCUIT_BREAKER_MAX_FAILURES: int = int(os.getenv("CIRCUIT_BREAKER_MAX_FAILURES", "5"))
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "60"))
    
    # Configuración de reintentos
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF_FACTOR: float = float(os.getenv("RETRY_BACKOFF_FACTOR", "0.5"))
    
    def get_cors_origins_list(self) -> List[str]:
        """Convierte CORS_ORIGINS de string a lista"""
        if self.CORS_ORIGINS.startswith("[") and self.CORS_ORIGINS.endswith("]"):
            try:
                return json.loads(self.CORS_ORIGINS)
            except json.JSONDecodeError:
                return ["*"]
        return [self.CORS_ORIGINS]
    
    def get_api_keys_list(self) -> List[str]:
        """Convierte API_KEYS de string a lista"""
        return [key.strip() for key in self.API_KEYS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
