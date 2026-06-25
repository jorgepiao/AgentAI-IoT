from typing import Any

from src.agent.skills.base import Skill, ToolDefinition
from src.core.guardrails import DEVICE_REGISTRY


class ClimateSkill(Skill):
    name: str = "clima"
    description: str = (
        "Control de climatización: aire acondicionado, calefacción, "
        "ajuste de temperatura y modos de operación"
    )
    keywords: list[str] = [
        "frío", "calor", "temperatura", "clima", "ac",
        "calefacción", "aire acondicionado", "calefactor",
        "enfriar", "calentar", "grados",
    ]

    def get_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="set_temperature",
                description="Fijar la temperatura de un dispositivo de clima",
                parameters={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "ID del dispositivo",
                            "enum": self._climate_device_ids,
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperatura objetivo en °C",
                            "minimum": 16,
                            "maximum": 30,
                        },
                    },
                    "required": ["device_id", "temperature"],
                },
            ),
            ToolDefinition(
                name="set_climate_mode",
                description="Cambiar el modo de operación del clima",
                parameters={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "ID del dispositivo",
                            "enum": self._climate_device_ids,
                        },
                        "mode": {
                            "type": "string",
                            "description": "Modo de operación",
                            "enum": ["cool", "heat", "fan", "auto", "dry"],
                        },
                    },
                    "required": ["device_id", "mode"],
                },
            ),
            ToolDefinition(
                name="turn_off_climate",
                description="Apagar un dispositivo de climatización",
                parameters={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "ID del dispositivo",
                            "enum": self._climate_device_ids,
                        },
                    },
                    "required": ["device_id"],
                },
            ),
        ]

    @property
    def _climate_device_ids(self) -> list[str]:
        return [
            did for did, cfg in DEVICE_REGISTRY.items()
            if cfg["type"] == "climate"
        ]

    def execute_tool(
        self, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        if tool_name == "set_temperature":
            return {
                "device_id": params["device_id"],
                "action": "set_temperature",
                "params": {"temperature": params["temperature"]},
            }
        if tool_name == "set_climate_mode":
            return {
                "device_id": params["device_id"],
                "action": "set_mode",
                "params": {"mode": params["mode"]},
            }
        if tool_name == "turn_off_climate":
            return {
                "device_id": params["device_id"],
                "action": "off",
                "params": {},
            }

        raise ValueError(f"Herramienta desconocida: {tool_name}")
