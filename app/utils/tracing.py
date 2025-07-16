import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, DEPLOYMENT_ENVIRONMENT
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, DEPLOYMENT_ENVIRONMENT
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from fastapi import FastAPI
import logging
from typing import Optional, Callable, Any, TypeVar, cast
from functools import wraps
import inspect

# Definir tipos genéricos para los wrappers
F = TypeVar('F', bound=Callable[..., Any])

logger = logging.getLogger(__name__)

# Variable global para almacenar la configuración
try:
    from ..config.settings import get_settings
    settings = get_settings()
except ImportError:
    # Configuración por defecto si no se puede importar settings
    class DefaultSettings:
        OTEL_ENABLED = False
        OTEL_SERVICE_NAME = "automoviles-service"
        ENVIRONMENT = "development"
        OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4317"
    
    settings = DefaultSettings()

def setup_tracing(app: Optional[FastAPI] = None) -> Optional[TracerProvider]:
    """Configura la instrumentación de OpenTelemetry para la aplicación."""
    if not getattr(settings, 'OTEL_ENABLED', False):
        logger.info("OpenTelemetry está deshabilitado en la configuración")
        return None
    
    try:
        # Configurar el proveedor de trazas
        resource = Resource.create({
            SERVICE_NAME: getattr(settings, 'OTEL_SERVICE_NAME', 'automoviles-service'),
            DEPLOYMENT_ENVIRONMENT: getattr(settings, 'ENVIRONMENT', 'development'),
        })
        
        tracer_provider = TracerProvider(resource=resource)
        
        # Configurar el exportador OTLP
        otlp_exporter = OTLPSpanExporter(
            endpoint=getattr(settings, 'OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4317'),
            insecure=True
        )
        
        # Configurar el procesador de lotes
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        # Establecer el proveedor de trazas global
        trace.set_tracer_provider(tracer_provider)
        
        # Instrumentar FastAPI si se proporciona una aplicación
        if app is not None:
            FastAPIInstrumentor.instrument_app(
                app,
                tracer_provider=tracer_provider,
                excluded_urls="/health,/metrics"
            )
        
        logger.info("OpenTelemetry configurado correctamente")
        return tracer_provider
    
    except Exception as e:
        logger.error("Error al configurar OpenTelemetry: %s", str(e), exc_info=True)
        # Si hay un error, usar un proveedor sin procesador (no-op)
        trace.set_tracer_provider(TracerProvider())
        return None

def get_tracer(name: Optional[str] = None) -> trace.Tracer:
    """
    Obtiene un tracer de OpenTelemetry.
    
    Args:
        name: Nombre del módulo o componente que usará el tracer.
              Si no se proporciona, se usará el nombre del módulo que llama.
    
    Returns:
        Un objeto Tracer de OpenTelemetry.
    """
    if not name:
        # Obtener el nombre del módulo que llama
        frame = inspect.currentframe()
        try:
            if frame is not None and frame.f_back is not None:
                name = frame.f_back.f_globals.get('__name__', 'unknown')
            else:
                name = 'unknown'
        finally:
            # Importante: eliminar la referencia al frame para evitar problemas de referencia circular
            del frame
    
    return trace.get_tracer(name)

def trace_function(
    name: Optional[str] = None, 
    kind: trace.SpanKind = trace.SpanKind.INTERNAL
) -> Callable[[F], F]:
    """
    Decorador para instrumentar funciones con trazas de OpenTelemetry.
    
    Args:
        name: Nombre del span. Si no se proporciona, se usará el nombre de la función.
        kind: Tipo de span (SERVER, CLIENT, INTERNAL, etc.)
    
    Returns:
        Un decorador que envuelve la función con trazas de OpenTelemetry.
    """
    def decorator(func: F) -> F:
        # Obtener el nombre del span del nombre de la función si no se proporciona
        span_name = name or f"{func.__module__}.{func.__qualname__}"
        
        # Si la función es asíncrona, usar el wrapper asíncrono
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                tracer = get_tracer(func.__module__)
                with tracer.start_as_current_span(span_name, kind=kind) as span:
                    try:
                        result = await func(*args, **kwargs)  # type: ignore
                        return result
                    except Exception as e:
                        # Registrar el error en el span
                        if span.is_recording():
                            span.record_exception(e)
                            span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
            return cast(F, async_wrapper)
        
        # Si la función es síncrona, usar el wrapper síncrono
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer(func.__module__)
            with tracer.start_as_current_span(span_name, kind=kind) as span:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Registrar el error en el span
                    if span.is_recording():
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        
        return cast(F, sync_wrapper)
    
    return decorator
