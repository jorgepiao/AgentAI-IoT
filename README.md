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
│   │       └── lighting.py  # Skill de iluminación (focos/dimmers)
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

### Ejecución

```bash
# Modo simulación (sin hardware, recomendado para desarrollo)
uvicorn src.main:app --reload

# La API estará disponible en http://localhost:8000
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

## Licencia

MIT
