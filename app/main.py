import logging
import time
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request, Depends, HTTPException, status, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse, HTMLResponse
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge
from opentelemetry import trace

from .routers import automoviles
from .config.settings import get_settings
from .utils.logger import setup_logging, logger
from .utils.tracing import setup_tracing, get_tracer

# Configuración inicial
settings = get_settings()

# Configuración de logging
setup_logging()

# Métricas de Prometheus
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code', 'service']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'service']
)
ACTIVE_REQUESTS = Gauge(
    'http_requests_in_progress',
    'Number of requests in progress',
    ['method', 'endpoint', 'service']
)

# Configuración de seguridad
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Claves API válidas (en producción, usa una base de datos o un servicio de gestión de secretos)
VALID_API_KEYS = {
    "test-key": "test-user",
    "prod-key": "prod-user"
}

async def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    """Valida la clave API proporcionada en el encabezado."""
    if api_key_header in VALID_API_KEYS:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="API key inválida o faltante"
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación."""
    # Inicialización
    logger.info("Iniciando la aplicación...")
    
    # Configurar OpenTelemetry
    if settings.OTEL_ENABLED:
        setup_tracing(app)
    
    yield
    
    # Limpieza al apagar
    logger.info("Apagando la aplicación...")

# Crear la aplicación FastAPI
app = FastAPI(
    title="API de Automóviles",
    description="API para la gestión de un inventario de automóviles con características de resiliencia",
    version="1.0.0",
    docs_url=None,  # Deshabilitar docs por defecto
    redoc_url=None,  # Deshabilitar redoc por defecto
    openapi_url="/openapi.json" if settings.DEBUG else None,  # Ocultar en producción
    lifespan=lifespan
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para métricas, logs y manejo de errores
@app.middleware("http")
async def metrics_and_logging_middleware(request: Request, call_next):
    """Middleware para registrar métricas, logs y manejar errores."""
    start_time = time.time()
    
    # Obtener información de la ruta
    endpoint = request.url.path
    method = request.method
    
    # Incrementar contador de solicitudes activas
    ACTIVE_REQUESTS.labels(
        method=method,
        endpoint=endpoint,
        service="automoviles"
    ).inc()
    
    try:
        # Procesar la solicitud
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Registrar métricas
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=response.status_code,
            service="automoviles"
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=method,
            endpoint=endpoint,
            service="automoviles"
        ).observe(process_time)
        
        # Registrar log de la solicitud
        logger.info(
            f"{method} {endpoint} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.4f}s",
            extra={
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "duration": process_time,
                "client": request.client.host if request.client else "unknown"
            }
        )
        
        return response
    
    except Exception as e:
        process_time = time.time() - start_time
        status_code = getattr(e, 'status_code', 500)
        
        # Registrar error en métricas
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            service="automoviles"
        ).inc()
        
        # Registrar error en logs
        logger.error(
            f"Error en {method} {endpoint}: {str(e)}",
            exc_info=True,
            extra={
                "method": method,
                "endpoint": endpoint,
                "status_code": status_code,
                "duration": process_time,
                "error": str(e)
            }
        )
        
        # Devolver respuesta de error
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": str(e),
                "error": e.__class__.__name__
            } if settings.DEBUG else {
                "detail": "Internal Server Error"
            }
        )
    
    finally:
        # Decrementar contador de solicitudes activas
        ACTIVE_REQUESTS.labels(
            method=method,
            endpoint=endpoint,
            service="automoviles"
        ).dec()

# Health Check
@app.get(
    "/health",
    tags=["Sistema"],
    summary="Verificar el estado del servicio",
    description="Endpoint para verificar que el servicio está en funcionamiento.",
    response_description="Estado del servicio"
)
async def health_check():
    """Verifica el estado del servicio."""
    return {
        "status": "healthy",
        "service": "api-automoviles",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

# Ruta raíz
@app.get(
    "/",
    tags=["Sistema"],
    summary="Página de bienvenida",
    description="Endpoint raíz que proporciona información básica sobre la API.",
    response_description="Mensaje de bienvenida"
)
async def root():
    """Endpoint raíz que devuelve un mensaje de bienvenida."""
    return {
        "message": "Bienvenido al API de Automóviles",
        "version": "1.0.0",
        "documentation": "/docs" if settings.DEBUG else None,
        "environment": settings.ENVIRONMENT
    }

# Documentación de la API (solo en modo desarrollo)
if settings.DEBUG:
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"API de Automóviles - {settings.ENVIRONMENT.upper()}",
            swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png"
        )
    
    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url="/openapi.json",
            title=f"API de Automóviles - {settings.ENVIRONMENT.upper()}",
            redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png"
        )

# Incluir routers
app.include_router(
    automoviles.router,
    prefix="/api/v1/automoviles",
    tags=["Automóviles"],
    dependencies=[Depends(get_api_key)]  # Requiere autenticación
)

# Montar el servidor de métricas
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Configuración personalizada de OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="API de Automóviles",
        version="1.0.0",
        description="API para la gestión de un inventario de automóviles con características de resiliencia",
        routes=app.routes,
    )
    
    # Personalizar documentación de autenticación
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": API_KEY_NAME,
            "description": "Ingresa la clave API en el encabezado: `X-API-Key: tu-clave-aqui`"
        }
    }
    
    # Asegurar que todas las rutas requieran autenticación
    if "security" not in openapi_schema:
        openapi_schema["security"] = [{"ApiKeyAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Aplicar esquema OpenAPI personalizado
app.openapi = custom_openapi

# Punto de entrada principal
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level="info" if settings.DEBUG else "warning"
    )
