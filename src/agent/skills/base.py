from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]


class Skill(BaseModel, ABC):
    name: str
    description: str
    keywords: list[str] = []

    @abstractmethod
    def get_tools(self) -> list[ToolDefinition]:
        ...

    @abstractmethod
    def execute_tool(
        self, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        ...

    def matches(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.keywords)
