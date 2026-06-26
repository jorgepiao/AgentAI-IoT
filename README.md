# AgentAI IoT

**Ecosistema de Automatización Residencial Edge-Native con IA Local**

Sistema de agente único cognitivo que integra Modelos de Lenguaje de Frontera (Frontier LLMs) ejecutados localmente con redes de hardware asíncronas mediante MQTT. Todo el procesamiento ocurre en el borde de la red (Edge-Native), garantizando **soberanía total de datos** — cero dependencia de nube, cero telemetría externa.

---

## Filosofía del Proyecto

AgentAI IoT no es un asistente de voz convencional. Es un **sistema de control físico soberano** donde la inteligencia artificial actúa como capa de razonamiento, pero la validación final de cada comando recae en capas deterministas (Guardrails de Pydantic). Esto asegura que ningún error de alucinación del LLM pueda traducirse en un daño físico al hardware del hogar.

### Principios de Diseño

| Principio | Implementación |
|-----------|---------------|
| **Soberanía de Datos** | Procesamiento 100% local via Ollama/vLLM. Sin conexión a APIs externas. |
| **Desacoplamiento Físico** | Sandbox de simulación permite desarrollar y validar todo el sistema sin hardware real. Se migra a físico cambiando variables de entorno. |
| **Eficiencia Cognitiva** | Sistema dinámico de Skills que carga en memoria solo el módulo relevante para cada consulta, reduciendo tokens y latencia. |
| **Seguridad por Capas** | El LLM **nunca** publica directamente en MQTT. Todo comando pasa por validación Pydantic antes de ser despachado. |

---

## Arquitectura

```
[Usuario (Voz/Texto)]
       │
       ▼
[FastAPI Gateway] ────> [Skill Router] ────> [Inyección de Skills (Pydantic)]
                                                    │
                                         (Prompt Optimizado)
                                                    │
                                                    ▼
[Broker MQTT (Mosquitto)] <─── [Tool Calling] <─── [LLM Local (Inferencia)]
       │
       ├── (Prefijo "sim/") ───> [Sandbox de Simulación Virtual]
       └── (Prefijo "home/") ──> [Hardware Físico Real (ESP32/Raspberry Pi)]
```

## Seguridad

AgentAI IoT incorpora seguridad en múltiples capas:

### Soberanía de Datos
- Todo el procesamiento es local. No hay envío de datos a servicios cloud.
- El LLM corre en la misma red local via Ollama/vLLM.
- No se almacenan conversaciones ni telemetría fuera del dispositivo.

### Validación Determinista (Guardrails)
- El LLM tiene prohibido publicar directamente en MQTT.
- Todos los comandos generados por IA pasan por esquemas Pydantic v2 que verifican:
  - Existencia del dispositivo destino
  - Rango seguro de valores (temperatura máxima, nivel lumínico, etc.)
  - Formato correcto de parámetros
- Cualquier comando que no pase validación es abortado inmediatamente.

### Comunicación MQTT
- El broker Mosquitto se configura con autenticación básica (usuario/contraseña) como mínimo.
- Tópicos MQTT siguen una jerarquía clara: `sim/` y `home/` como prefijos de primer nivel.
- La caché de estado en memoria permite al LLM conocer el estado actual sin interrogar hardware en tiempo real, reduciendo tráfico en la red.

---

## Pilares Tecnológicos

| Capa | Tecnología |
|------|-----------|
| Lenguaje | Python 3.11+ (asíncrono, tipado estricto) |
| API Gateway | FastAPI + WebSockets |
| IA Local | Ollama / vLLM (localhost) |
| Validación | Pydantic v2 (Guardrails deterministas) |
| Mensajería IoT | MQTT via Eclipse Mosquitto |
| Simulación | Sandbox virtual sin hardware |
| Testing | pytest + httpx |

---

## Estructura del Proyecto

```
agentai-iot/
├── config/                  # Configuración del sistema (.env)
│   ├── settings.py          # Carga de variables de entorno
│   └── mqtt_config.py       # Configuración del broker MQTT
│
├── src/                     # Núcleo del software
│   ├── main.py              # Punto de entrada FastAPI
│   │
│   ├── agent/               # Capa Cognitiva
│   │   ├── engine.py        # Orquestador de inferencia local
│   │   ├── AGENT.md         # Manifiesto operativo del agente
│   │   └── skills/          # Módulos de Habilidades
│   │       ├── base.py      # Clase abstracta e interfaz común
│   │       ├── climate.py   # Skill de clima (AC/calefacción)
│   │       ├── cover.py     # Skill de persianas y cortinas
│   │       ├── fan.py       # Skill de ventilación
│   │       ├── lighting.py  # Skill de iluminación (focos/dimmers)
│   │       └── switch.py    # Skill de on/off (enchufes, cafeteras)
│   │
│   ├── core/                # Infraestructura de red y seguridad
│   │   ├── mqtt_client.py   # Cliente MQTT asíncrono + caché
│   │   └── guardrails.py    # Esquemas Pydantic de validación
│   │
│   └── utils/               # Utilidades (logs, excepciones)
│
├── simulation/              # Sandbox de hardware virtual
│   ├── mock_sensors.py      # Simula envío de telemetría
│   └── mock_actuadores.py   # Simula recepción de comandos
│
├── tests/                   # Pruebas unitarias y de integración
├── .env.template            # Plantilla de configuración
├── requirements.txt
└── README.md
```

---

## Inicio Rápido

### Prerrequisitos

- Python 3.11+
- Ollama instalado y corriendo (o vLLM)
- Eclipse Mosquitto (opcional en modo simulación)

### Instalación

```bash
# 1. Clonar y entrar
git clone https://github.com/tu-usuario/agentai-iot.git
cd agentai-iot

# 2. Entorno virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
# source .venv/bin/activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Configurar entorno
cp .env.template .env
# Editar .env con tu configuración local
```

### Ejecución (3 ventanas)

```powershell
# Abre API + sensores + actuadores cada uno en su propia ventana
.\scripts\run_all.ps1
```

O manualmente, cada componente en una terminal separada:

```bash
# Terminal 1 — API
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Sensores simulados
python -m simulation.mock_sensors --dry-run --interval 5

# Terminal 3 — Actuadores simulados
python -m simulation.mock_actuadores --dry-run
```

### Verificación

```bash
# Health check
curl http://localhost:8000/health

# Enviar un comando
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Enciende las luces de la sala"}'
```

## Docker

### Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo

### Servicios

| Servicio | Imagen | Puerto |
|---|---|---|
| `mosquitto` | `eclipse-mosquitto:2` | `1883` |
| `api` | Construida desde `Dockerfile` | `8000` |

### Uso

```bash
# Construir la imagen de la API (solo la primera vez o al cambiar requirements.txt)
docker compose build

# Levantar todos los servicios en segundo plano
docker compose up -d

# Ver logs en tiempo real (opcional)
docker compose logs -f

# Verificar que la API responde
curl http://localhost:8000/health

# Ejecutar simuladores (en otra terminal, fuera del contenedor)
python -m simulation.mock_sensors --dry-run --interval 5
python -m simulation.mock_actuadores --dry-run

# Abrir el dashboard
start dashboard.html

# Detener todo
docker compose down
```

**Nota:** Los cambios en `src/` se reflejan automáticamente gracias al volumen montado y `--reload`. Solo necesitas reconstruir si agregas dependencias a `requirements.txt`.

**Importante para producción:** No uses este `docker-compose.yml` en producción sin antes:
1. Quitar `volumes` (el código debe ir dentro de la imagen)
2. Quitar `--reload` 
3. Configurar autenticación en Mosquitto (`allow_anonymous false`)
4. Usar credenciales seguras via `.env`

## Dashboard de Prueba

Interfaz web independiente para probar el sistema visualmente.

```
agentai-iot/
├── dashboard.html    ← Ábrelo en el navegador (archivo único, sin dependencias)
└── scripts/          ← Herramientas CLI (próximamente)
```

**Cómo usarlo:**

1. Inicia el servidor: `uvicorn src.main:app --reload`
2. Abre `dashboard.html` en Chrome/Edge (doble click)
3. El dashboard se conecta automáticamente a `http://localhost:8000`

**Qué muestra:**

| Panel | Descripción |
|-------|-------------|
| Chat | Envía comandos en lenguaje natural, ve las respuestas validadas |
| Dispositivos | Estado actual de luces, clima, persianas, ventiladores, enchufes y cafetera |
| Sensores | Lecturas de telemetría (temperatura, humedad, luminosidad, movimiento, puerta) |
| Skills | Herramientas disponibles por cada skill |
| Trazas | Historial de llamadas API y eventos del sistema |

**Agregar nuevos dispositivos o sensores:**

Edita los arreglos `DEVICES` o `SENSORS` al inicio del `<script>` en `dashboard.html`:

```javascript
const DEVICES = [
  { id: "cocina.luz", room: "Cocina", label: "Luz", icon: "💡", type: "light" },
  // ...
];
const SENSORS = [
  { topic: "cocina/sensor/temperatura", room: "Cocina", label: "Temperatura", unit: "°C", icon: "🌡️" },
  // ...
];
```

El dashboard renderiza automáticamente las nuevas entradas.

## Licencia

MIT
