import pytest

from src.agent.skills.climate import ClimateSkill
from src.agent.skills.base import ToolDefinition


@pytest.fixture
def skill():
    return ClimateSkill()


class TestClimateSkillCreation:
    def test_name_and_description(self, skill):
        assert skill.name == "clima"
        assert len(skill.description) > 0

    def test_keywords(self, skill):
        assert "temperatura" in skill.keywords
        assert "calor" in skill.keywords
        assert "frío" in skill.keywords


class TestClimateSkillMatching:
    def test_match_frio(self, skill):
        assert skill.matches("hace mucho frío en la sala") is True

    def test_match_temperatura(self, skill):
        assert skill.matches("sube la temperatura a 24 grados") is True

    def test_no_match(self, skill):
        assert skill.matches("enciende las luces") is False


class TestClimateToolDefinitions:
    def test_tools_count(self, skill):
        tools = skill.get_tools()
        assert len(tools) == 3

    def test_tool_names(self, skill):
        names = [t.name for t in tools] if (tools := skill.get_tools()) else []
        assert "set_temperature" in names
        assert "set_climate_mode" in names
        assert "turn_off_climate" in names

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
                assert "sala.aire_acondicionado" in device_enum
                assert "dormitorio.calefactor" in device_enum


class TestClimateExecuteTool:
    def test_set_temperature(self, skill):
        result = skill.execute_tool("set_temperature", {
            "device_id": "sala.aire_acondicionado",
            "temperature": 24,
        })
        assert result["device_id"] == "sala.aire_acondicionado"
        assert result["action"] == "set_temperature"
        assert result["params"]["temperature"] == 24

    def test_set_climate_mode(self, skill):
        result = skill.execute_tool("set_climate_mode", {
            "device_id": "dormitorio.calefactor",
            "mode": "heat",
        })
        assert result["device_id"] == "dormitorio.calefactor"
        assert result["action"] == "set_mode"
        assert result["params"]["mode"] == "heat"

    def test_turn_off_climate(self, skill):
        result = skill.execute_tool("turn_off_climate", {
            "device_id": "sala.aire_acondicionado",
        })
        assert result["device_id"] == "sala.aire_acondicionado"
        assert result["action"] == "off"
        assert result["params"] == {}

    def test_unknown_tool_raises(self, skill):
        with pytest.raises(ValueError, match="Herramienta desconocida"):
            skill.execute_tool("nonexistent", {"device_id": "sala.aire_acondicionado"})
