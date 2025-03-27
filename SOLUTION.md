# Practica-liberando-productos-Guillermo-Rodrigues-Botias
Practica liberando productos Guillermo Rodrigues Botias


## INDICE

* [*Primera parte*](#primera-parte) : Objetivo, Requisitos y Estructura
* [*Segunda parte*](#segunda-parte) : Archivos necesarios
* [*Tercera parte*](#tercera-parte) : Configuracion 

## Primera Parte

En esta practica vamos a partir del siguiente repositorio 
```bash https://github.com/KeepCodingCloudDevops11/liberando-productos-practica-final.git ```, haremos un fork y sobre el aplicaremos nuestros cambios cambios. Es una aplicación basada en FastAPI desplegada en kubernetes.

* Tendrá las siguientes funcionalidades:
- Desarrollo y extensión de una API con un nuevo endpoint.
- Creación de test unitarios.
- Integración continua y despliegue con GitHub Actions y GHCR.
- Monitorización de métricas con Prometheus.
- Alertas automáticas con AlertManager.
- Integración de notificaciones en Slack.
- Visualzación de KPIs en un dashboard de Grafana.

* ESTRUCTURA

```bash
Practica liberando-productos Guillermo Rodrigues/
│ 
├──.github
│  └── workflows
│        ├── release.yaml 
│        └── test.yaml
│
│
├── .pytest_cache
│
├── garafana
│   └── fastapi-dashboard.json
│
├── htmlcov
│
│
├── src/
│    ├── test
│    ├──   ├──__pycache__
│    │     ├──__init__.py
│    │     └──app_test.py
│    │
│    ├── venv
│    ├── app.py
│    └── application/
│        ├── __pycache__
│        ├── __init__.py
│        ├── venv
│        └── app.py               # Código de FastAPI con métricas
│
├── venv
│
├── .coverage
│
├── Makefile
│
├── pytest.ini
│
├── README.md
│
├── SOLUTION.md
│
├── requirements.txt
│
├── Dockerfile
│
├── helm-values/
│   ├── kube-state-values.yaml  # Config extra para kube-state-metrics
│   ├── alertmanager-config.yaml # Config webhook Slack
│   └── additional-rules.yaml   # Reglas de alerta personalizadas
│
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── fastapi-servicemonitor.yaml
│   └── cpu-test-app.yamlc
```

* Los requisitos previos son:

1. Tener creado los secretos en GitHub, ```GHCR_USER, GHCR_TOKEN```

2. Helm instalado

3. Docker funcionado y arrancamos con ```bash minikube start```. Debemos tener la imagen DOcker funcional, en este caso será ```guillermors28/simple-server:0.0.6```

4. Crear el canal de Slack, seguidamente crear Webhook entrante y añadir esa url como secreto para CI/CD
5. Test ya configurados.

6. Prometheus instalado, podemo usando ```bash kube-prometheus-stack``` vía Helm, configurando las reglas y alertas con el archivo additional-rules.yaml. El serciemonitor funcioando y apuntando a puerto (8000)

7. AlertManager configurado con Slack, el archivo alertmanager.yaml tiene ```slack_configs``` y las alertas con severidad critica.

8. Dashboard en Grafana, abriremos el servico con ```bash kubectl port-forward svc/kube-prometheus-stack-grafana -n monitoring 3000:80``` y accederemos con admin y por defecto prom-operator. Importamos nuestro **fastapi-dashboard.json** para ver nuestro panel ya configurado.

## Segunda PArte

* Los archivos que tenemos que crear o modificar son:

#### test.yaml

```bash
name: Test Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Check out code
        uses: actions/checkout@v3

      - name: Setup Python 3.9
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests with coverage
        run: pytest --cov=.

```

#### release.yaml

```bash
name: Release Pipeline

on:
  push:
    branches:
      - main

jobs:
  build-and-push:
    runs-on: ubuntu-latest

    steps:
      - name: Check out code
        uses: actions/checkout@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ secrets.GHCR_USER }}
          password: ${{ secrets.GHCR_TOKEN }}

      - name: Build Docker image
        run: |
          IMAGE_NAME=ghcr.io/${{ secrets.GHCR_USER }}/mi-fastapi-app:${{ github.sha }}
          docker build -t $IMAGE_NAME .

      - name: Push Docker image
        run: |
          IMAGE_NAME=ghcr.io/${{ secrets.GHCR_USER }}/mi-fastapi-app:${{ github.sha }}
          docker push $IMAGE_NAME

      - name: Replace Slack webhook in Alertmanager config
        run: |
          sed -i "s|https://hooks.slack.com/services/PLACEHOLDER|${{ secrets.SLACK_WEBHOOK_URL }}|" helm-values/alertmanager-config.yaml
```

#### fastapi-dashboard.json

```bash
{
    "title": "FastAPI Dashboard",
    "panels": [
      {
        "type": "stat",
        "title": "Llamadas a /",
        "targets": [{"expr": "main_requests_total"}],
        "gridPos": { "x": 0, "y": 0, "w": 6, "h": 4 }
      },
      {
        "type": "stat",
        "title": "Llamadas a /health",
        "targets": [{"expr": "healthcheck_requests_total"}],
        "gridPos": { "x": 6, "y": 0, "w": 6, "h": 4 }
      },
      {
        "type": "stat",
        "title": "Llamadas a /bye",
        "targets": [{"expr": "bye_requests_total"}],
        "gridPos": { "x": 0, "y": 4, "w": 6, "h": 4 }
      },
      {
        "type": "stat",
        "title": "Reinicios de la App",
        "targets": [{"expr": "fastapi_app_starts_total"}],
        "gridPos": { "x": 6, "y": 4, "w": 6, "h": 4 }
      },
      {
        "type": "stat",
        "title": "Uso actual de CPU (real)",
        "targets": [
          {
            "expr": "sum by(pod) (rate(container_cpu_usage_seconds_total{namespace=\"default\", pod=~\"fastapi.*\"}[2m]))"
          }
        ],
        "gridPos": { "x": 0, "y": 8, "w": 6, "h": 4 }
      },
      {
        "type": "stat",
        "title": "CPU Request asignado",
        "targets": [
          {
            "expr": "sum by(pod) (kube_pod_container_resource_requests_cpu_cores{namespace=\"default\", pod=~\"fastapi.*\"})"
          }
        ],
        "gridPos": { "x": 6, "y": 8, "w": 6, "h": 4 }
      },
      {
        "type": "table",
        "title": "Alertas Activas",
        "targets": [{"expr": "ALERTS{alertstate=\"firing\"}"}],
        "gridPos": { "x": 0, "y": 12, "w": 12, "h": 6 }
      },
      {
        "type": "stat",
        "title": "Reinicios del contenedor",
        "targets": [
          {
            "expr": "rate(kube_pod_container_status_restarts_total{namespace=\"default\"}[5m])"
          }
        ],
        "gridPos": { "x": 0, "y": 18, "w": 6, "h": 4 }
      },
      {
        "type": "stat",
        "title": "Total de peticiones",
        "targets": [{"expr": "server_requests_total"}],
        "gridPos": { "x": 6, "y": 18, "w": 6, "h": 4 }
      }
    ],
    "schemaVersion": 35,
    "version": 1,
    "refresh": "5s"
  }
```

#### additional-rules.yaml

```bash
additionalPrometheusRules:
  - name: fastapi-cpu-alert
    groups:
      - name: fastapi.rules
        rules:
          - alert: FastApiCustomCpuAlert
            expr: fastapi_cpu_usage > fastapi_cpu_request
            for: 1m
            labels:
              severity: high
            annotations:
              summary: "High CPU usage on FastAPI container"
              description: "Simulated CPU usage exceeds request in FastAPI container."

          - alert: TestSlackAlert
            expr: increase(bye_requests_total[2m]) > 5
            for: 30s
            labels:
              severity: critical
            annotations:
              summary: "⚠️ Alerta de prueba para Slack"
              description: "Se ha accedido al endpoint /bye más de 5 veces en los últimos 2 minutos"
```
#### alertmanager-config.yaml

```bash
alertmanager:
  config:
    global:
      resolve_timeout: 5m

    route:
      group_by: ['alertname', 'job']
      group_wait: 10s
      group_interval: 30s
      repeat_interval: 1h
      receiver: 'slack-notifications'
      routes:
        - matchers:
            - severity="critical"
          receiver: 'slack-notifications'

    receivers:
      - name: 'slack-notifications'
        slack_configs:
          - send_resolved: true
            channel: '#guillermo-prometheus-alarms'   # Canal real
            username: 'PrometheusBot'
            icon_emoji: ':rotating_light:'
            api_url: 'https://hooks.slack.com/services/PLACEHOLDER'
            title: "*[{{ .Status | toUpper }}]* {{ .CommonLabels.alertname }}"
            text: >
              {{ range .Alerts }}
              *Alert:* {{ .Annotations.summary }}
              *Description:* {{ .Annotations.description }}
              *Severity:* {{ .Labels.severity }}
              *Starts At:* {{ .StartsAt }}
              *Ends At:* {{ .EndsAt }}
              {{ end }}
```

#### kube-state-values.yaml

```bash
kube-state-metrics:
  prometheusScrape: true
  selfMonitor:
    enabled: true
  metricLabelsAllowlist:
    - pods=[*]
    - deployments=[*]
  metricAllowlist:
    - kube_pod_container_resource_requests_cpu_cores
    - kube_pod_container_resource_limits_cpu_cores
    - kube_pod_container_resource_requests_memory_bytes
    - kube_pod_container_resource_limits_memory_bytes
```

#### cpu-test-app.yaml

```bash
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  labels:
    app: fastapi-app
    app.kubernetes.io/name: fastapi-app
    app.kubernetes.io/instance: fastapi-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
        app.kubernetes.io/name: fastapi-app
        app.kubernetes.io/instance: fastapi-app
        app.kubernetes.io/component: web
    spec:
      containers:
        - name: fastapi
          image: guillermors28/simple-server:0.0.6
          ports:
            - name: http
              containerPort: 8081
            - name: metrics
              containerPort: 8000
          resources:
            requests:
              cpu: "100m"
            limits:
              cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
  labels:
    app: fastapi-app
    release: kube-prometheus-stack
spec:
  selector:
    app: fastapi-app
  ports:
    - name: http
      port: 80
      targetPort: 8081
    - name: metrics
      port: 8000
      targetPort: 8000
  type: ClusterIP
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: fastapi-monitor
  namespace: monitoring
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchLabels:
      app: fastapi-app
  namespaceSelector:
    matchNames:
      - default
  endpoints:
    - port: metrics
      path: /metrics
      interval: 15s
```

#### deployment.yaml

```bash
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  labels:
    app: fastapi-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
    spec:
      containers:
        - name: fastapi
          image: guillermors28/simple-server:0.0.6
          ports:
            - containerPort: 8081
              name: http
            - containerPort: 8000
              name: metrics
          resources:
            requests:
              cpu: "100m"
            limits:
              cpu: "200m"
```
#### fastapi-servicemonitor.yaml

```bash
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: fastapi-monitor
  namespace: monitoring
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchLabels:
      app: fastapi-app
  namespaceSelector:
    matchNames:
      - default
  endpoints:
    - port: metrics
      path: /metrics
      interval: 15s
```

#### service.yaml

```bash
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
  labels:
    app: fastapi-app
    release: kube-prometheus-stack
spec:
  selector:
    app: fastapi-app
  ports:
    - name: http
      port: 80
      targetPort: 8081
    - name: metrics
      port: 8000
      targetPort: 8000
  type: ClusterIP
```

#### src/test/app_test.py

```bash
"""
Module used for testing simple server module
"""

from fastapi.testclient import TestClient
import pytest

from application.app import app

client = TestClient(app)

class TestSimpleServer:
    """
    TestSimpleServer class for testing SimpleServer
    """
    @pytest.mark.asyncio
    async def read_health_test(self):
        """Tests the health check endpoint"""
        response = client.get("health")

        assert response.status_code == 200
        assert response.json() == {"health": "ok"}

    @pytest.mark.asyncio
    async def read_main_test(self):
        """Tests the main endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        assert response.json() == {"msg": "Hello World"}

    @pytest.mark.asyncio
    async def read_bye_test(self):
        """Tests the main endpoint"""
        response = client.get("/bye")

        assert response.status_code == 200
        assert response.json() == {"msg": "Bye Bye"}
```

#### src/app.py

```bash
"""
Module for launch application
"""

import asyncio

from prometheus_client import start_http_server
from application.app import SimpleServer


class Container:
    """
    Class Container configure necessary methods for launch application
    """

    def __init__(self):
        self._simple_server = SimpleServer()

    async def start_server(self):
        """Function for start server"""
        await self._simple_server.run_server()


if __name__ == "__main__":
    start_http_server(8000)
    container = Container()
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(container.start_server(), loop=loop)
    loop.run_forever()
```

#### src/application/app.py

```bash
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

# ESTE CONTADOR DE ARRANQUE
APP_STARTS = Counter('fastapi_app_starts_total', 'App boot counter')
APP_STARTS.inc() # Esto debe ejecutarse UNA vez al inicio

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
```
#### Dockerfile

```bash
FROM python:3.8.11-alpine3.14

WORKDIR /service/app
ADD ./src/ /service/app/
COPY requirements.txt /service/app/

RUN apk --no-cache add curl build-base npm \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

EXPOSE 8081
EXPOSE 8000

ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=5 \
    CMD curl -s --fail http://localhost:8081/health || exit 1

CMD ["python3", "-u", "app.py"]
```
#### requirements.txt

```bash
fastapi==0.115.4
hypercorn==0.17.3
dnspython==2.6.1
email-validator==2.2.0
pylint==3.2.7
pytest==8.3.3
coverage==7.6.1
pytest-cov==5.0.0
pytest-asyncio==0.24.0
uvicorn==0.32.0
certifi==2024.8.30
charset-normalizer==3.4.0
requests==2.32.3
urllib3==2.2.3
prometheus-client==0.21.0
httpx==0.27.2
uvicorn
```

## Tercera Parte

**Docker**

* Nos saeguramos que esta corriendo. Una vez tenemos nuestra estructura creada y los archivos correctamente, podemos crear un entrono virtual y verificamos que los test son correctos:

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
[Entorno virtual](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Prueba%20app.py%20con%20modificaciones.png)


y ejecutamos los test:
```bash
pytest
pytest --cov
pytest --cov --cov-report=html
```

[Test](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/TEst%20con%20nuevo%20endpoint.png)
[Test2](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Test%20completos.png)


* Construimos la imagen y la arrancamos, recordar que cada cambio en ficheros habrá que volver a ejceutar:

```bash
CONSTRUIR IMAGEN NUEVA
docker build -t guillermors28/simple-server:0.0.6 .
docker push guillermors28/simple-server:0.0.6
kubectl set image deploy/fastapi-app fastapi=guillermors28/simple-server:0.0.6
docker run -d -p 8000:8000 -p 8081:8081 --name simple-server guillermors28/simple-server:0.0.6
```
[Aplicaicon funcionando](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/App%20funcionando.png)
[Prueba local bye](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Captura%20de%20pantalla%202025-03-24%20212033.png)
[Metricas local bye](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Captura%20de%20pantalla%202025-03-26%20152913.png)


* **Desplegamos aplicación en kubernetes**


```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/service-monitor.yaml
```

Y verificamos:
```bash
kubectl get pods
kubectl get svc
kubectl get servicemonitor -n monitoring
```

* **GitHub** 

Configuramos las variables de entorno.

* Hacmos un push en la rama main de nuestro proyecto a Github, en la pestaña Actions podemos ver el estado y los test.
[GitHub ACtions ok](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Actions%20ok.png)


* Podemos obtener los logs del contendor ynos dará:
```bash docker logs -f simple-server```
[2022-04-16 09:44:22 +0000] [1] [INFO] Running on http://0.0.0.0:8081 (CTRL + C to quit)

* Para probar podemo hacer 
```bash python app.py``` lo podemos hacer en el entorno virtual creado, si no nos funciona instalamos los paquetes:
```bash
pip install prometheus_client
pip install hypercorn prometheus_client
pip install -r requirements.txt
pip list
```

* Podemos abrir puerto ```bash kubectl port-forward svc/fastapi-service 8081:80``` y probar
```bash curl http://localhost:8081/ -H "accept: application/json -v"``` esto para main, lo mismo para /heatlh y /bye. 
Para ver las métricas acabara ```curl http://localhost:8000/metrics``` y cada vez que se acceda a un servicio veremos como incrementa en métricas.

[Métricas](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/M%C3%A9tricas.png)
[GitHub Actions](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/pipline%20CICD%20github%20actions.png)

* **Prometheus**

- Descargamos e instalamos Prometheus.

```bash
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace

helm upgrade kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring \
  -f helm-values/alertmanager-config.yaml \
  -f helm-values/additional-rules.yaml \
  -f helm-values/kube-state-values.yaml
```
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

[Prometheus up](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Target%20up.png)

* Verificamos Prometheus

En la carpeta raíz donde se encuentre el archivo

```bash
.\prometheus.exe --config.file=prometheus.yml
```
también podemos abrir puerto
```bash
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
```
y entramos con ```http://localhost:9090``` en el navegador.

[Otra forma de acceder](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Captura%20de%20pantalla%202025-03-26%20153703.png)

En la pestaña de status/target vemos que todo este UP.

En la parte de Graph, en query podemos ver el consumo de cpu con ```bash sum(rate(container_cpu_usage_seconds_total{namespace="default", pod=~"fastapi.*"}[2m])) by (pod)```

En alerts veremos las dos alertas configuradas, de cpu y acceso de más de cinco veces a bye, irán camabiado de estado FIRING a RESOLVED en función si cumplen las condiciones o no.

[Alerta cpu](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/firing%20cpu.png)
[Alertas FIRING](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Captura%20de%20pantalla%202025-03-25%20164619.png)
[Alerta pending](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Captura%20de%20pantalla%202025-03-26%20172218.png)
[Alerta resuelta](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Captura%20de%20pantalla%202025-03-25%20212836.png)
[FIRING + RESOLVED](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/firing%20%2B%20resolved%20cpu.png)

Para acceder a la interfaz de Alertmanager
```bash
kubectl port-forward svc/kube-prometheus-stack-alertmanager 9093:9093 -n monitoring
```
En el navegador con ```http://localhost:9093``` veremos si se activan.

[Prometheus Targets](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Prometheus%20target.png)
[Lectura Prometheus](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Lectura%20cpu%20prometehus.png)
[Prometheus bye](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Prometheus%20bye.png)
[Prometheus health](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Prometheus%20health.png)
[Prometheus main](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Prometheus%20main.png)
[Prometheus server](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Prometheus%20server.png)

* **Slack**

Creamos un secreto en github llamado ```SLACK_WEBHOOK_URL``` y lo configuramos con el webhook de Slack

Accedemos a nuestro Slack y creamos un canal.
- Creamos un Webhook entrante, nos dará la url para nuestro archivo alertmanager.yaml.
- Aplicamos la configuración helm, desde nuestro proyecto para actualizarlo.
- Aplicamos ```bash kubectl port-forward svc/kube-prometheus-stack-alertmanager -n monitoring 9093:9093``` y accedemos al navegador ```http://localhost:9093``` y veremos las alertas.

[Webhooks](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Slack.png)

[FIRING bye](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Resolved%20slack.png)
[RESOLVED bye](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Resolved.png)

* **Grafana**

Para acceder a Grafana hacemos que este disponible primero

```bash
kubectl port-forward svc/kube-prometheus-stack-grafana -n monitoring 3000:80
```
y entramos a traves del navegador con ```http://localhost:3000```. Al acceder por primera vez, las credenciales por defecto son
- Usuario: admin
- Password: prom-operator

Ahora tenemos que crear un nuevo dashboard, como ya tenemos nuestro archivo configuramos podemos importarlo desde la interfaz. En los paneles podremos ver el uso de CPU así como las veces que se reinicia, alertas, llamadas a servicios...

Para hacer pruebas y ver los valores cambiar en Grafana hacemos

```bash
kubectl port-forward svc/fastapi-service 8081:80
```
y las peticiones ```curl http://localhost:8081/bye```  ```curl http://localhost:8081/health```  ```curl http://localhost:8081```

[Lectura Grafana](https://github.com/GuilleRsB/Practica-final-liberando-productos-Guillermo-Rodrigues/blob/main/img%20cambios%20aplicados/Grafana.png)




---
Creado por: Guillermo Rodrigues BOtias  
© 2025