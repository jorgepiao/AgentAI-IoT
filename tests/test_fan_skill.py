import pytest

from src.agent.skills.fan import FanSkill
from src.agent.skills.base import ToolDefinition


@pytest.fixture
def skill():
    return FanSkill()


class TestFanSkillCreation:
    def test_name_and_description(self, skill):
        assert skill.name == "ventilacion"
        assert len(skill.description) > 0

    def test_keywords(self, skill):
        assert "ventilador" in skill.keywords
        assert "velocidad" in skill.keywords
        assert "viento" in skill.keywords


class TestFanSkillMatching:
    def test_match_ventilador(self, skill):
        assert skill.matches("prende el ventilador de la sala") is True

    def test_match_velocidad(self, skill):
        assert skill.matches("pon el ventilador al 50 por ciento") is True

    def test_no_match(self, skill):
        assert skill.matches("baja la persiana") is False


class TestFanToolDefinitions:
    def test_tools_count(self, skill):
        tools = skill.get_tools()
        assert len(tools) == 3

    def test_tool_names(self, skill):
        tools = skill.get_tools()
        names = [t.name for t in tools]
        assert "turn_on_fan" in names
        assert "turn_off_fan" in names
        assert "set_fan_speed" in names

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
                assert "sala.ventilador" in device_enum


class TestFanExecuteTool:
    def test_turn_on_fan(self, skill):
        result = skill.execute_tool("turn_on_fan", {
            "device_id": "sala.ventilador",
        })
        assert result["device_id"] == "sala.ventilador"
        assert result["action"] == "on"
        assert result["params"] == {}

    def test_turn_off_fan(self, skill):
        result = skill.execute_tool("turn_off_fan", {
            "device_id": "sala.ventilador",
        })
        assert result["device_id"] == "sala.ventilador"
        assert result["action"] == "off"
        assert result["params"] == {}

    def test_set_fan_speed(self, skill):
        result = skill.execute_tool("set_fan_speed", {
            "device_id": "sala.ventilador",
            "speed": 75,
        })
        assert result["device_id"] == "sala.ventilador"
        assert result["action"] == "set_speed"
        assert result["params"]["speed"] == 75

    def test_unknown_tool_raises(self, skill):
        with pytest.raises(ValueError, match="Herramienta desconocida"):
            skill.execute_tool("nonexistent", {"device_id": "sala.ventilador"})
