"""
Module define fastapi server configuration
"""

from fastapi import FastAPI
from fastapi.responses import Response
from hypercorn.asyncio import serve
from hypercorn.config import Config as HyperCornConfig
from prometheus_client import (
    Counter,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST
)
import threading
import time

app = FastAPI()

# Métricas Prometheus
REQUESTS = Counter('server_requests_total', 'Total number of requests to this webserver')
HEALTHCHECK_REQUESTS = Counter('healthcheck_requests_total', 'Total number of requests to healthcheck')
MAIN_ENDPOINT_REQUESTS = Counter('main_requests_total', 'Total number of requests to main endpoint')
BYE_ENDPOINT_REQUESTS = Counter('bye_requests_total', 'Total number of requests to the /bye endpoint')

# Métricas simuladas para alerta de CPU
CPU_REQUEST = Gauge('fastapi_cpu_request', 'Simulated CPU request for FastAPI')
CPU_USAGE = Gauge('fastapi_cpu_usage', 'Simulated CPU usage for FastAPI')
CPU_REQUEST.set(0.1)  # simulamos 100m como request

# Función que consume CPU por un tiempo limitado y actualiza la métrica
def consume_cpu_temporarily():
    end_time = time.time() + 180  # 3 minutos
    while time.time() < end_time:
        _ = 1 + 1
        CPU_USAGE.set(0.3)  # Simulamos 300m de uso
        time.sleep(1)
    
    # Simulamos resolución de la alerta
    CPU_USAGE.set(0.05)  # Menor que request (0.1) → RESOLVED

# Lanza el hilo al iniciar
threading.Thread(target=consume_cpu_temporarily, daemon=True).start()

class SimpleServer:
    """
    SimpleServer class define FastAPI configuration and implemented endpoints
    """

    _hypercorn_config = None

    def __init__(self):
        self._hypercorn_config = HyperCornConfig()

    async def run_server(self):
        """Starts the server with the config parameters"""
        self._hypercorn_config.bind = ['0.0.0.0:8081']
        self._hypercorn_config.keep_alive_timeout = 90
        await serve(app, self._hypercorn_config)

# Endpoints de la API
@app.get("/health")
async def health_check():
    REQUESTS.inc()
    HEALTHCHECK_REQUESTS.inc()
    return {"health": "ok"}

@app.get("/")
async def read_main():
    REQUESTS.inc()
    MAIN_ENDPOINT_REQUESTS.inc()
    return {"msg": "Hello World"}

@app.get("/bye")
async def read_bye():
    REQUESTS.inc()
    BYE_ENDPOINT_REQUESTS.inc()
    return {"msg": "Bye Bye"}

# Endpoint para métricas
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Bloque para lanzar el servidor
if __name__ == '__main__':
    import asyncio
    server = SimpleServer()
    asyncio.run(server.run_server())
