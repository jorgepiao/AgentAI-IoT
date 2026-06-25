from typing import Any

from src.agent.skills.base import Skill, ToolDefinition
from src.core.guardrails import DEVICE_REGISTRY


class LightingSkill(Skill):
    name: str = "iluminacion"
    description: str = (
        "Control de iluminación: encendido, apagado, ajuste de brillo "
        "y activación de escenas de luz"
    )
    keywords: list[str] = [
        "luz", "luces", "ilumina", "foco", "focos",
        "brillo", "iluminación", "lámpara", "lámparas",
        "prende", "apaga", "escena", "atenuar",
    ]

    def get_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="set_light_state",
                description="Encender o apagar un dispositivo de iluminación",
                parameters={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "ID del dispositivo",
                            "enum": self._light_device_ids,
                        },
                        "state": {
                            "type": "string",
                            "description": "Estado deseado",
                            "enum": ["on", "off"],
                        },
                    },
                    "required": ["device_id", "state"],
                },
            ),
            ToolDefinition(
                name="set_brightness",
                description="Ajustar el nivel de brillo de una luz",
                parameters={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "ID del dispositivo",
                            "enum": self._light_device_ids,
                        },
                        "brightness": {
                            "type": "integer",
                            "description": "Nivel de brillo (0-100)",
                            "minimum": 0,
                            "maximum": 100,
                        },
                    },
                    "required": ["device_id", "brightness"],
                },
            ),
        ]

    @property
    def _light_device_ids(self) -> list[str]:
        return [
            did for did, cfg in DEVICE_REGISTRY.items()
            if cfg["type"] == "light"
        ]

    def execute_tool(
        self, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        if tool_name == "set_light_state":
            return {
                "device_id": params["device_id"],
                "action": params["state"],
                "params": {},
            }
        if tool_name == "set_brightness":
            return {
                "device_id": params["device_id"],
                "action": "set_brightness",
                "params": {"brightness": params["brightness"]},
            }

        raise ValueError(f"Herramienta desconocida: {tool_name}")
