from typing import Any

from src.agent.skills.base import Skill, ToolDefinition
from src.core.guardrails import DEVICE_REGISTRY


class FanSkill(Skill):
    name: str = "ventilacion"
    description: str = (
        "Control de ventiladores de techo y ventilación: "
        "encendido, apagado y ajuste de velocidad"
    )
    keywords: list[str] = [
        "ventilador", "ventiladores", "abanico", "fan",
        "viento", "ventilación", "ventilacion",
        "velocidad", "oscilar",
    ]

    def get_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="turn_on_fan",
                description="Encender un ventilador",
                parameters={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "ID del dispositivo",
                            "enum": self._fan_device_ids,
                        },
                    },
                    "required": ["device_id"],
                },
            ),
            ToolDefinition(
                name="turn_off_fan",
                description="Apagar un ventilador",
                parameters={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "ID del dispositivo",
                            "enum": self._fan_device_ids,
                        },
                    },
                    "required": ["device_id"],
                },
            ),
            ToolDefinition(
                name="set_fan_speed",
                description="Ajustar la velocidad de un ventilador (0-100%)",
                parameters={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "ID del dispositivo",
                            "enum": self._fan_device_ids,
                        },
                        "speed": {
                            "type": "integer",
                            "description": "Velocidad en porcentaje (0-100)",
                            "minimum": 0,
                            "maximum": 100,
                        },
                    },
                    "required": ["device_id", "speed"],
                },
            ),
        ]

    @property
    def _fan_device_ids(self) -> list[str]:
        return [
            did for did, cfg in DEVICE_REGISTRY.items()
            if cfg["type"] == "fan"
        ]

    def execute_tool(
        self, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        if tool_name == "turn_on_fan":
            return {
                "device_id": params["device_id"],
                "action": "on",
                "params": {},
            }
        if tool_name == "turn_off_fan":
            return {
                "device_id": params["device_id"],
                "action": "off",
                "params": {},
            }
        if tool_name == "set_fan_speed":
            return {
                "device_id": params["device_id"],
                "action": "set_speed",
                "params": {"speed": params["speed"]},
            }

        raise ValueError(f"Herramienta desconocida: {tool_name}")
