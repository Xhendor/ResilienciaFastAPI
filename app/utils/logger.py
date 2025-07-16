import logging
import sys
from pythonjsonlogger import jsonlogger
from typing import Dict, Any
import json
from datetime import datetime

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

        # Agregar información del logger
        log_record['logger'] = record.name
        
        # Agregar información de la traza si está disponible
        if hasattr(record, 'otelSpanID') and record.otelSpanID:
            log_record['span_id'] = record.otelSpanID
        if hasattr(record, 'otelTraceID') and record.otelTraceID:
            log_record['trace_id'] = record.otelTraceID
        
        # Manejo de excepciones
        if record.exc_info and not log_record.get('exception'):
            log_record['exception'] = self.formatException(record.exc_info)

        # Limpiar campos duplicados
        log_record.pop('message', None)
        log_record.pop('asctime', None)

        # Agregar el mensaje principal
        if record.msg and isinstance(record.msg, dict):
            log_record.update(record.msg)
        elif record.msg:
            log_record['message'] = record.getMessage()
        
        # Agregar campos adicionales si están presentes
        if hasattr(record, 'custom_fields') and isinstance(record.custom_fields, dict):
            log_record.update(record.custom_fields)

def setup_logging():
    """Configura el sistema de logging de la aplicación."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Eliminar manejadores existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Configurar formato
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        timestamp=True
    )
    
    # Configurar salida a consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configurar filtro para logs de acceso de uvicorn
    class EndpointFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return record.args and len(record.args) > 2 and record.args[2] != "/health"
    
    # Aplicar filtro para evitar logs de health check
    console_handler.addFilter(EndpointFilter())
    
    # Agregar manejador
    logger.addHandler(console_handler)
    
    # Configurar nivel de logging para bibliotecas externas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    
    return logger

# Inicializar el logger al importar el módulo
logger = setup_logging()
