"""
Module define fastapi server configuration
"""

from fastapi import FastAPI
from hypercorn.asyncio import serve
from hypercorn.config import Config as HyperCornConfig
from prometheus_client import Counter
from fastapi.responses import Response

app = FastAPI()

REQUESTS = Counter('server_requests_total', 'Total number of requests to this webserver')
HEALTHCHECK_REQUESTS = Counter('healthcheck_requests_total', 'Total number of requests to healthcheck')
MAIN_ENDPOINT_REQUESTS = Counter('main_requests_total', 'Total number of requests to main endpoint')
BYE_REQUESTS = Counter('bye_requests_total', 'Total number of requests to the bye endpoint')
BYE_REQUESTS.inc(0)

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

    @app.get("/health")
    async def health_check():
        """Implement health check endpoint"""
        # Increment counter used for register the total number of calls in the webserver
        REQUESTS.inc()
        # Increment counter used for register the requests to healtcheck endpoint
        HEALTHCHECK_REQUESTS.inc()
        return {"health": "ok"}

    @app.get("/")
    async def read_main():
        """Implement main endpoint"""
        # Increment counter used for register the total number of calls in the webserver
        REQUESTS.inc()
        # Increment counter used for register the total number of calls in the main endpoint
        MAIN_ENDPOINT_REQUESTS.inc()
        return {"msg": "Hello World"}
    
    @app.get("/bye")
    async def read_bye():
        print("Se llamó al endpoint /bye")
        """Implement bye endpoint"""
        # Increment counter used for register the total number of calls in the webserver
        REQUESTS.inc()
        # Increment counter used for register the total number of calls in the main endpoint
        BYE_REQUESTS.inc()
        return {"msg": "Bye Bye"}

# Endpoint para exponer las métricas a Prometheus
@app.get("/metrics")
async def metrics():
    """Devuelve todas las métricas en formato Prometheus."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Bloque principal para ejecutar la aplicación
if __name__ == '__main__':
    import asyncio
    server = SimpleServer()
    asyncio.run(server.run_server())
