import pytest

from src.agent.skills.lighting import LightingSkill
from src.agent.skills.base import ToolDefinition


@pytest.fixture
def skill():
    return LightingSkill()


class TestLightingSkillCreation:
    def test_name_and_description(self, skill):
        assert skill.name == "iluminacion"
        assert len(skill.description) > 0

    def test_keywords(self, skill):
        assert "luz" in skill.keywords
        assert "luces" in skill.keywords
        assert "brillo" in skill.keywords


class TestLightingSkillMatching:
    def test_match_luces(self, skill):
        assert skill.matches("enciende las luces de la sala") is True

    def test_match_brillo(self, skill):
        assert skill.matches("sube el brillo al máximo") is True

    def test_no_match(self, skill):
        assert skill.matches("pon el clima a 22 grados") is False


class TestLightingToolDefinitions:
    def test_tools_count(self, skill):
        tools = skill.get_tools()
        assert len(tools) == 2

    def test_tool_names(self, skill):
        tools = skill.get_tools()
        names = [t.name for t in tools]
        assert "set_light_state" in names
        assert "set_brightness" in names

    def test_tool_definitions_are_tool_definition_instances(self, skill):
        for tool in skill.get_tools():
            assert isinstance(tool, ToolDefinition)

    def test_device_ids_in_enum(self, skill):
        tools = skill.get_tools()
        for tool in tools:
            device_enum = (
                tool.parameters.get("properties", {})
                .get("device_id", {})
                .get("enum", [])
            )
            if device_enum:
                assert "sala.luz_principal" in device_enum
                assert "oficina.luz_escritorio" in device_enum


class TestLightingExecuteTool:
    def test_turn_on(self, skill):
        result = skill.execute_tool("set_light_state", {
            "device_id": "sala.luz_principal",
            "state": "on",
        })
        assert result["device_id"] == "sala.luz_principal"
        assert result["action"] == "on"
        assert result["params"] == {}

    def test_turn_off(self, skill):
        result = skill.execute_tool("set_light_state", {
            "device_id": "oficina.luz_escritorio",
            "state": "off",
        })
        assert result["device_id"] == "oficina.luz_escritorio"
        assert result["action"] == "off"
        assert result["params"] == {}

    def test_set_brightness(self, skill):
        result = skill.execute_tool("set_brightness", {
            "device_id": "sala.luz_principal",
            "brightness": 75,
        })
        assert result["device_id"] == "sala.luz_principal"
        assert result["action"] == "set_brightness"
        assert result["params"]["brightness"] == 75

    def test_unknown_tool_raises(self, skill):
        with pytest.raises(ValueError, match="Herramienta desconocida"):
            skill.execute_tool("nonexistent", {"device_id": "sala.luz_principal"})
