from typing import List, Optional, Dict, Any
from datetime import datetime
import random
import time
import logging
from circuitbreaker import circuit, CircuitBreakerError
from functools import wraps
import httpx
from fastapi import HTTPException, status

from ..models.automovil import AutomovilCreate, AutomovilUpdate, AutomovilInDB, Database, EstadoAutomovil

logger = logging.getLogger(__name__)

db = Database()

# Configuración del Circuit Breaker
def failure_callback(response):
    return response.status_code >= 500 if hasattr(response, 'status_code') else False

# Decorador para reintentos con backoff exponencial
def retry_with_backoff(retries=3, backoff_in_seconds=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        logger.error(f"Max retries reached: {str(e)}")
                        raise
                    else:
                        wait = backoff_in_seconds * (2 ** x) + random.uniform(0, 1)
                        logger.warning(f"Retry {x + 1}/{retries} - waiting {wait:.2f} seconds: {str(e)}")
                        time.sleep(wait)
                        x += 1
        return wrapper
    return decorator

class AutomovilService:
    @circuit(failure_threshold=5, recovery_timeout=60, expected_exception=HTTPException)
    @retry_with_backoff(retries=3)
    async def crear_automovil(self, automovil: AutomovilCreate) -> AutomovilInDB:
        try:
            # Simular una llamada externa que podría fallar
            await self._simular_llamada_externa()
            
            nuevo_automovil = AutomovilInDB(
                id=db.get_next_id(),
                **automovil.model_dump(),
                fecha_creacion=datetime.now(),
                fecha_actualizacion=datetime.now()
            )
            db.automoviles[nuevo_automovil.id] = nuevo_automovil
            return nuevo_automovil
        except Exception as e:
            logger.error(f"Error al crear automóvil: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error al procesar la solicitud"
            )

    @circuit(failure_threshold=5, recovery_timeout=60)
    @retry_with_backoff(retries=3)
    async def obtener_automoviles(self) -> List[AutomovilInDB]:
        try:
            # Simular una llamada externa que podría fallar
            await self._simular_llamada_externa()
            return list(db.automoviles.values())
        except Exception as e:
            logger.error(f"Error al obtener automóviles: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error al obtener los automóviles"
            )

    @circuit(failure_threshold=5, recovery_timeout=60)
    @retry_with_backoff(retries=3)
    async def obtener_automovil_por_id(self, automovil_id: str) -> Optional[AutomovilInDB]:
        try:
            # Simular una llamada externa que podría fallar
            await self._simular_llamada_externa()
            
            automovil = db.automoviles.get(automovil_id)
            if not automovil:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Automóvil no encontrado"
                )
            return automovil
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error al obtener automóvil {automovil_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error al obtener el automóvil"
            )

    @circuit(failure_threshold=5, recovery_timeout=60)
    @retry_with_backoff(retries=3)
    async def actualizar_automovil(
        self, automovil_id: str, automovil_actualizado: AutomovilUpdate
    ) -> Optional[AutomovilInDB]:
        try:
            # Simular una llamada externa que podría fallar
            await self._simular_llamada_externa()
            
            if automovil_id not in db.automoviles:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Automóvil no encontrado"
                )
            
            automovil_actual = db.automoviles[automovil_id]
            update_data = automovil_actualizado.model_dump(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(automovil_actual, field, value)
            
            automovil_actual.fecha_actualizacion = datetime.now()
            db.automoviles[automovil_id] = automovil_actual
            
            return automovil_actual
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error al actualizar automóvil {automovil_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error al actualizar el automóvil"
            )

    @circuit(failure_threshold=5, recovery_timeout=60)
    @retry_with_backoff(retries=3)
    async def eliminar_automovil(self, automovil_id: str) -> bool:
        try:
            # Simular una llamada externa que podría fallar
            await self._simular_llamada_externa()
            
            if automovil_id not in db.automoviles:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Automóvil no encontrado"
                )
            
            del db.automoviles[automovil_id]
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error al eliminar automóvil {automovil_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error al eliminar el automóvil"
            )

    async def _simular_llamada_externa(self):
        """
        Simula una llamada externa que tiene un 20% de probabilidad de fallar
        para probar los reintentos y el circuit breaker.
        """
        if random.random() < 0.2:  # 20% de probabilidad de fallo
            logger.warning("¡Error simulado en llamada externa!")
            raise Exception("Error simulado en servicio externo")
