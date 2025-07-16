from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from ..models.automovil import AutomovilCreate, AutomovilUpdate, AutomovilInDB, EstadoAutomovil
from ..services.automovil_service import AutomovilService
from opentelemetry import trace

router = APIRouter(tags=["automoviles"])
service = AutomovilService()

tracer = trace.get_tracer(__name__)

@router.post("/", response_model=AutomovilInDB, status_code=status.HTTP_201_CREATED)
async def crear_automovil(automovil: AutomovilCreate):
    """
    Crea un nuevo automóvil en el inventario.
    """
    with tracer.start_as_current_span("crear_automovil"):
        return await service.crear_automovil(automovil)

@router.get("/", response_model=List[AutomovilInDB])
async def listar_automoviles(estado: Optional[EstadoAutomovil] = None):
    """
    Obtiene la lista de todos los automóviles, opcionalmente filtrados por estado.
    """
    with tracer.start_as_current_span("listar_automoviles"):
        automoviles = await service.obtener_automoviles()
        if estado:
            return [a for a in automoviles if a.estado == estado]
        return automoviles

@router.get("/{automovil_id}", response_model=AutomovilInDB)
async def obtener_automovil(automovil_id: str):
    """
    Obtiene los detalles de un automóvil específico por su ID.
    """
    with tracer.start_as_current_span("obtener_automovil") as span:
        span.set_attribute("automovil_id", automovil_id)
        return await service.obtener_automovil_por_id(automovil_id)

@router.put("/{automovil_id}", response_model=AutomovilInDB)
async def actualizar_automovil(
    automovil_id: str, automovil_actualizado: AutomovilUpdate
):
    """
    Actualiza los datos de un automóvil existente.
    """
    with tracer.start_as_current_span("actualizar_automovil") as span:
        span.set_attribute("automovil_id", automovil_id)
        return await service.actualizar_automovil(automovil_id, automovil_actualizado)

@router.delete("/{automovil_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_automovil(automovil_id: str):
    """
    Elimina un automóvil del inventario.
    """
    with tracer.start_as_current_span("eliminar_automovil") as span:
        span.set_attribute("automovil_id", automovil_id)
        await service.eliminar_automovil(automovil_id)
        return None

# Endpoint para probar el circuit breaker
@router.get("/test/circuit-breaker")
async def test_circuit_breaker():
    """
    Endpoint para probar el funcionamiento del circuit breaker.
    Tiene un 50% de probabilidad de fallar para probar los reintentos.
    """
    with tracer.start_as_current_span("test_circuit_breaker"):
        import random
        if random.random() < 0.5:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error simulado para probar el circuit breaker"
            )
        return {"status": "success", "message": "¡Operación exitosa!"}
