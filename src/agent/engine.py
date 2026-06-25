import json
import logging
from typing import Any, Callable, Coroutine

from pydantic import ValidationError

from config.settings import settings
from src.agent.skills.base import Skill
from src.core.guardrails import validate_command

logger = logging.getLogger(__name__)

LLMCallable = Callable[[str], Coroutine[Any, Any, str]]


class Engine:
    def __init__(self) -> None:
        self.skills: dict[str, Skill] = {}

    def register_skill(self, skill: Skill) -> None:
        self.skills[skill.name] = skill
        logger.info("Skill registrado: %s (%s)", skill.name, skill.description)

    def detect_skill(self, message: str) -> Skill | None:
        for skill in self.skills.values():
            if skill.matches(message):
                logger.debug("Skill detectado: %s para mensaje: %s", skill.name, message)
                return skill
        return None

    def build_prompt(self, message: str, skill: Skill) -> str:
        tools = skill.get_tools()
        tools_json = json.dumps([t.model_dump() for t in tools], indent=2, ensure_ascii=False)

        return (
            f"Eres un asistente de control de hogar inteligente.\n"
            f"Skill activo: {skill.name} — {skill.description}\n\n"
            f"Herramientas disponibles:\n{tools_json}\n\n"
            f"Instrucciones:\n"
            f"- Responde ÚNICAMENTE con un objeto JSON.\n"
            f"- No agregues texto adicional, explicaciones ni formato markdown.\n"
            f"- El JSON debe tener esta estructura:\n"
            f'  {{"device_id": "...", "action": "...", "params": {{...}}}}\n\n'
            f"Mensaje del usuario: {message}"
        )

    async def process(
        self,
        message: str,
        llm_callable: LLMCallable | None = None,
    ) -> dict[str, Any]:
        skill = self.detect_skill(message)
        if skill is None:
            return {"error": "No se reconoció el comando", "message": message}

        prompt = self.build_prompt(message, skill)

        if llm_callable is not None:
            response = await llm_callable(prompt)
        else:
            response = await self._call_ollama(prompt)

        return self._parse_response(response, skill)

    def _parse_response(
        self, raw: str, skill: Skill
    ) -> dict[str, Any]:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            return {"error": f"Respuesta LLM no es JSON válido: {exc}", "raw": raw}

        try:
            validated = validate_command(data)
            return {
                "skill": skill.name,
                "device_id": validated.device_id,
                "action": validated.action,
                "params": validated.params,
                "validated": True,
            }
        except (ValueError, ValidationError) as exc:
            return {"error": f"Comando rechazado por guardrails: {exc}", "raw": data}

    async def _call_ollama(self, prompt: str) -> str:
        raise NotImplementedError(
            "LLM no configurado. Proporciona un llm_callable o configura Ollama."
        )


engine = Engine()
