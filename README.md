# API de Automóviles con FastAPI

Este es un proyecto de ejemplo que implementa una API RESTful para gestionar un inventario de automóviles utilizando FastAPI, con características avanzadas de resiliencia y observabilidad.

## Características

- 🔄 **Retry y Timeouts**: Mecanismos de reintento y tiempos de espera para llamadas externas
- 🧯 **Circuit Breaker**: Patrón Circuit Breaker para prevenir fallos en cascada
- 📊 **Observabilidad**: Logs, métricas y trazas con OpenTelemetry
- ✅ **Health Checks**: Endpoints para verificar el estado del servicio
- 🧪 **Pruebas de estrés**: Configuración para pruebas de carga
- 📦 **Contenedorizado**: Configuración lista para Docker y Docker Compose

## Requisitos

- Python 3.9+
- Docker y Docker Compose
- OPCIONAL: Jaeger, Prometheus y Grafana para monitoreo

## Configuración

1. Clona el repositorio:
   ```bash
   git clone <repo-url>
   cd ResilienciaFastAPI
   ```

2. Crea un entorno virtual y activa:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configura las variables de entorno (copia .env.example a .env y ajusta según sea necesario):
   ```bash
   cp .env.example .env
   ```

## Ejecución

### Opción 1: Ejecución local

```bash
uvicorn app.main:app --reload
```

### Opción 2: Con Docker Compose (recomendado)

```bash
docker-compose up --build
```

La aplicación estará disponible en: http://localhost:8000

## Documentación de la API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Monitoreo

- **Jaeger UI**: http://localhost:16686
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (usuario: admin, contraseña: admin)

## Estructura del Proyecto

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # Punto de entrada de la aplicación
│   ├── config/
│   │   └── settings.py      # Configuración de la aplicación
│   ├── models/
│   │   └── automovil.py     # Modelos de datos
│   ├── routers/
│   │   └── automoviles.py   # Endpoints de la API
│   ├── services/
│   │   └── automovil_service.py  # Lógica de negocio
│   └── utils/
│       ├── logger.py        # Configuración de logging
│       └── tracing.py       # Configuración de OpenTelemetry
├── tests/                   # Pruebas unitarias y de integración
├── .env                    # Variables de entorno
├── .gitignore
├── docker-compose.yml      # Configuración de Docker Compose
├── Dockerfile              # Dockerfile para la aplicación
├── otel-collector-config.yaml  # Configuración de OpenTelemetry Collector
├── prometheus.yml          # Configuración de Prometheus
└── requirements.txt        # Dependencias de Python
```

## Uso de la API

### Autenticación

La API utiliza autenticación por API Key. Incluye el siguiente encabezado en tus solicitudes:

```
X-API-Key: test-key
```

### Ejemplos de Uso

#### Crear un automóvil

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/automoviles/' \
  -H 'X-API-Key: test-key' \
  -H 'Content-Type: application/json' \
  -d '{
    "marca": "Toyota",
    "modelo": "Corolla",
    "año": 2022,
    "precio": 25000.0,
    "kilometraje": 0.0,
    "color": "Rojo"
  }'
```

#### Listar todos los automóviles

```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/automoviles/' \
  -H 'X-API-Key: test-key'
```

#### Obtener un automóvil por ID

```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/automoviles/1' \
  -H 'X-API-Key: test-key'
```

## Pruebas

Para ejecutar las pruebas:

```bash
pytest

```
Con environment
```bash

.\.venv\Scripts\activate; python -m pytest tests/ -v
```
## Licencia

Sin licencia a quien le interese usarlo para aprender. 

Enlace del Proyecto: [https://github.com/tuusuario/resiliencia-fastapi](https://github.com/tuusuario/resiliencia-fastapi)
