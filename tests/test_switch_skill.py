import pytest

from src.agent.skills.switch import SwitchSkill
from src.agent.skills.base import ToolDefinition


@pytest.fixture
def skill():
    return SwitchSkill()


class TestSwitchSkillCreation:
    def test_name_and_description(self, skill):
        assert skill.name == "interruptores"
        assert len(skill.description) > 0

    def test_keywords(self, skill):
        assert "enchufe" in skill.keywords
        assert "cafetera" in skill.keywords
        assert "prende" in skill.keywords


class TestSwitchSkillMatching:
    def test_match_enchufe(self, skill):
        assert skill.matches("apaga el enchufe de la oficina") is True

    def test_match_cafetera(self, skill):
        assert skill.matches("prende la cafetera") is True

    def test_no_match(self, skill):
        assert skill.matches("enciende las luces") is False


class TestSwitchToolDefinitions:
    def test_tools_count(self, skill):
        tools = skill.get_tools()
        assert len(tools) == 2

    def test_tool_names(self, skill):
        tools = skill.get_tools()
        names = [t.name for t in tools]
        assert "turn_on" in names
        assert "turn_off" in names

    def test_tool_definitions_are_tool_definition_instances(self, skill):
        for tool in skill.get_tools():
            assert isinstance(tool, ToolDefinition)

    def test_device_ids_in_enum_switch(self, skill):
        tools = skill.get_tools()
        for tool in tools:
            device_enum = (
                tool.parameters.get("properties", {})
                .get("device_id", {})
                .get("enum", [])
            )
            if device_enum:
                assert "oficina.enchufe" in device_enum
                assert "cocina.cafetera" in device_enum


class TestSwitchExecuteTool:
    def test_turn_on(self, skill):
        result = skill.execute_tool("turn_on", {
            "device_id": "cocina.cafetera",
        })
        assert result["device_id"] == "cocina.cafetera"
        assert result["action"] == "on"
        assert result["params"] == {}

    def test_turn_off(self, skill):
        result = skill.execute_tool("turn_off", {
            "device_id": "oficina.enchufe",
        })
        assert result["device_id"] == "oficina.enchufe"
        assert result["action"] == "off"
        assert result["params"] == {}

    def test_unknown_tool_raises(self, skill):
        with pytest.raises(ValueError, match="Herramienta desconocida"):
            skill.execute_tool("nonexistent", {"device_id": "cocina.cafetera"})
