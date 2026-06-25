from typing import Any

from src.agent.skills.base import Skill, ToolDefinition
from src.core.guardrails import DEVICE_REGISTRY


class SwitchSkill(Skill):
    name: str = "interruptores"
    description: str = (
        "Control de dispositivos on/off simples: enchufes inteligentes, "
        "electrodomésticos, cafeteras y otros aparatos"
    )
    keywords: list[str] = [
        "enchufe", "enchufes", "cafetera", "tomacorriente",
        "electrodoméstico", "electrodomestico", "aparato",
        "prende", "apaga", "encender", "apagar",
    ]

    def get_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="turn_on",
                description="Encender un dispositivo (enchufe, cafetera, etc.)",
                parameters={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "ID del dispositivo",
                            "enum": self._switchable_device_ids,
                        },
                    },
                    "required": ["device_id"],
                },
            ),
            ToolDefinition(
                name="turn_off",
                description="Apagar un dispositivo (enchufe, cafetera, etc.)",
                parameters={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "ID del dispositivo",
                            "enum": self._switchable_device_ids,
                        },
                    },
                    "required": ["device_id"],
                },
            ),
        ]

    @property
    def _switchable_device_ids(self) -> list[str]:
        return [
            did for did, cfg in DEVICE_REGISTRY.items()
            if cfg["type"] in ("switch", "appliance")
        ]

    def execute_tool(
        self, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        if tool_name in ("turn_on", "turn_off"):
            return {
                "device_id": params["device_id"],
                "action": tool_name.split("_")[1],
                "params": {},
            }

        raise ValueError(f"Herramienta desconocida: {tool_name}")
