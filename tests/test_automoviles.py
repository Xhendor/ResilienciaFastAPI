import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.automovil import AutomovilCreate, EstadoAutomovil

client = TestClient(app)

# Datos de prueba
TEST_AUTOMOVIL = {
    "marca": "Toyota",
    "modelo": "Corolla",
    "año": 2022,
    "precio": 25000.0,
    "estado": "disponible",
    "kilometraje": 0.0,
    "color": "Rojo"
}

# Clave API de prueba
TEST_API_KEY = "test-key"

def test_health_check():
    """Prueba el endpoint de health check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_crear_automovil():
    """Prueba la creación de un automóvil."""
    response = client.post(
        "/api/v1/automoviles/",
        json=TEST_AUTOMOVIL,
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["marca"] == "Toyota"
    assert data["modelo"] == "Corolla"
    assert data["estado"] == "disponible"
    return data["id"]

def test_obtener_automovil():
    """Prueba la obtención de un automóvil por ID."""
    # Primero creamos un automóvil
    automovil_id = test_crear_automovil()
    
    # Luego lo obtenemos
    response = client.get(
        f"/api/v1/automoviles/{automovil_id}",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == automovil_id
    assert data["marca"] == "Toyota"

def test_listar_automoviles():
    """Prueba el listado de automóviles."""
    response = client.get(
        "/api/v1/automoviles/",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_actualizar_automovil():
    """Prueba la actualización de un automóvil."""
    # Primero creamos un automóvil
    automovil_id = test_crear_automovil()
    
    # Datos de actualización
    datos_actualizacion = {
        "precio": 24000.0,
        "estado": "en_reparacion"
    }
    
    # Actualizamos el automóvil
    response = client.put(
        f"/api/v1/automoviles/{automovil_id}",
        json=datos_actualizacion,
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["precio"] == 24000.0
    assert data["estado"] == "en_reparacion"

def test_eliminar_automovil():
    """Prueba la eliminación de un automóvil."""
    # Primero creamos un automóvil
    automovil_id = test_crear_automovil()
    
    # Luego lo eliminamos
    response = client.delete(
        f"/api/v1/automoviles/{automovil_id}",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 204
    
    # Verificamos que ya no exista
    response = client.get(
        f"/api/v1/automoviles/{automovil_id}",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 404

def test_autenticacion_fallida():
    """Prueba el manejo de autenticación fallida."""
    response = client.get(
        "/api/v1/automoviles/",
        headers={"X-API-Key": "clave-invalida"}
    )
    assert response.status_code == 403
    assert "API key inválida" in response.text

def test_circuit_breaker():
    """Prueba el endpoint de prueba del circuit breaker."""
    # Este test puede fallar aleatoriamente debido a la simulación de fallos
    response = client.get(
        "/api/v1/automoviles/test/circuit-breaker",
        headers={"X-API-Key": TEST_API_KEY}
    )
    # Aceptamos tanto éxito como error 503 (Service Unavailable)
    assert response.status_code in [200, 503]
