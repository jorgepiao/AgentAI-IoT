from typing import Any

from src.agent.skills.base import Skill, ToolDefinition
from src.core.guardrails import DEVICE_REGISTRY


class CoverSkill(Skill):
    name: str = "persianas"
    description: str = (
        "Control de persianas y cortinas motorizadas: "
        "subir, bajar y ajustar posición"
    )
    keywords: list[str] = [
        "persiana", "persianas", "cortina", "cortinas",
        "subir", "bajar", "abrir persiana", "cerrar persiana",
        "blind", "blinds", "curtain",
    ]

    def get_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="open_cover",
                description="Subir o abrir completamente una persiana o cortina",
                parameters={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "ID del dispositivo",
                            "enum": self._cover_device_ids,
                        },
                    },
                    "required": ["device_id"],
                },
            ),
            ToolDefinition(
                name="close_cover",
                description="Bajar o cerrar completamente una persiana o cortina",
                parameters={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "ID del dispositivo",
                            "enum": self._cover_device_ids,
                        },
                    },
                    "required": ["device_id"],
                },
            ),
            ToolDefinition(
                name="set_cover_position",
                description="Ajustar la posición de una persiana o cortina (0=cerrada, 100=abierta)",
                parameters={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "ID del dispositivo",
                            "enum": self._cover_device_ids,
                        },
                        "position": {
                            "type": "integer",
                            "description": "Posición en porcentaje (0-100)",
                            "minimum": 0,
                            "maximum": 100,
                        },
                    },
                    "required": ["device_id", "position"],
                },
            ),
        ]

    @property
    def _cover_device_ids(self) -> list[str]:
        return [
            did for did, cfg in DEVICE_REGISTRY.items()
            if cfg["type"] == "cover"
        ]

    def execute_tool(
        self, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        if tool_name == "open_cover":
            return {
                "device_id": params["device_id"],
                "action": "open",
                "params": {},
            }
        if tool_name == "close_cover":
            return {
                "device_id": params["device_id"],
                "action": "close",
                "params": {},
            }
        if tool_name == "set_cover_position":
            return {
                "device_id": params["device_id"],
                "action": "set_position",
                "params": {"position": params["position"]},
            }

        raise ValueError(f"Herramienta desconocida: {tool_name}")
