import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import settings
from src.agent.engine import engine
from src.agent.skills.climate import ClimateSkill
from src.agent.skills.lighting import LightingSkill

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine.register_skill(ClimateSkill())
    engine.register_skill(LightingSkill())
    logger.info(
        "AgentAI IoT iniciado — modo: %s, prefijo MQTT: %s",
        settings.mode,
        settings.mqtt_topic_prefix,
    )
    yield


app = FastAPI(
    title="AgentAI IoT",
    version="1.1.0",
    description="API Gateway del ecosistema de automatización residencial con IA local",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "mode": settings.mode,
        "skills": list(engine.skills.keys()),
        "llm_model": settings.llm_model,
    }


@app.post("/chat")
async def chat(req: ChatRequest) -> dict:
    try:
        result = await engine.process(req.message)
        return result
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "LLM no configurado",
                "message": str(exc),
                "hint": "Proporciona un llm_callable o configura Ollama en .env",
            },
        )


@app.get("/skills")
async def list_skills() -> dict:
    return {
        name: {
            "description": skill.description,
            "keywords": skill.keywords,
            "tools": [t.model_dump() for t in skill.get_tools()],
        }
        for name, skill in engine.skills.items()
    }


@app.get("/state/{topic:path}")
async def get_device_state(topic: str) -> dict:
    from src.core.mqtt_client import mqtt_client

    if mqtt_client is not None and mqtt_client.is_connected:
        state = mqtt_client.get_state(topic)
        return {"topic": topic, "state": state}
    return {
        "topic": topic,
        "state": None,
        "note": "MQTT no conectado — el estado solo está disponible con un broker activo",
    }
