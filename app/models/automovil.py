from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class EstadoAutomovil(str, Enum):
    DISPONIBLE = "disponible"
    EN_REPARACION = "en_reparacion"
    VENDIDO = "vendido"

class AutomovilBase(BaseModel):
    marca: str = Field(..., min_length=2, max_length=50)
    modelo: str = Field(..., min_length=1, max_length=50)
    año: int = Field(..., gt=1900, le=datetime.now().year + 1)
    precio: float = Field(..., gt=0)
    estado: EstadoAutomovil = EstadoAutomovil.DISPONIBLE
    kilometraje: float = Field(..., ge=0)
    color: str = Field(..., min_length=3, max_length=30)

class AutomovilCreate(AutomovilBase):
    pass

class AutomovilUpdate(BaseModel):
    precio: Optional[float] = Field(None, gt=0)
    estado: Optional[EstadoAutomovil] = None
    kilometraje: Optional[float] = Field(None, ge=0)

class AutomovilInDB(AutomovilBase):
    id: str
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True

# Clase para simular la base de datos en memoria
class Database:
    def __init__(self):
        self.automoviles = {}
        self.current_id = 1
    
    def get_next_id(self) -> str:
        current = self.current_id
        self.current_id += 1
        return str(current)
