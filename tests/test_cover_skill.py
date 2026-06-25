import pytest

from src.agent.skills.cover import CoverSkill
from src.agent.skills.base import ToolDefinition


@pytest.fixture
def skill():
    return CoverSkill()


class TestCoverSkillCreation:
    def test_name_and_description(self, skill):
        assert skill.name == "persianas"
        assert len(skill.description) > 0

    def test_keywords(self, skill):
        assert "persiana" in skill.keywords
        assert "cortina" in skill.keywords
        assert "subir" in skill.keywords


class TestCoverSkillMatching:
    def test_match_persiana(self, skill):
        assert skill.matches("sube la persiana de la sala") is True

    def test_match_cortina(self, skill):
        assert skill.matches("baja la cortina") is True

    def test_no_match(self, skill):
        assert skill.matches("enciende las luces") is False


class TestCoverToolDefinitions:
    def test_tools_count(self, skill):
        tools = skill.get_tools()
        assert len(tools) == 3

    def test_tool_names(self, skill):
        tools = skill.get_tools()
        names = [t.name for t in tools]
        assert "open_cover" in names
        assert "close_cover" in names
        assert "set_cover_position" in names

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
                assert "sala.persiana" in device_enum


class TestCoverExecuteTool:
    def test_open_cover(self, skill):
        result = skill.execute_tool("open_cover", {
            "device_id": "sala.persiana",
        })
        assert result["device_id"] == "sala.persiana"
        assert result["action"] == "open"
        assert result["params"] == {}

    def test_close_cover(self, skill):
        result = skill.execute_tool("close_cover", {
            "device_id": "sala.persiana",
        })
        assert result["device_id"] == "sala.persiana"
        assert result["action"] == "close"
        assert result["params"] == {}

    def test_set_cover_position(self, skill):
        result = skill.execute_tool("set_cover_position", {
            "device_id": "sala.persiana",
            "position": 50,
        })
        assert result["device_id"] == "sala.persiana"
        assert result["action"] == "set_position"
        assert result["params"]["position"] == 50

    def test_unknown_tool_raises(self, skill):
        with pytest.raises(ValueError, match="Herramienta desconocida"):
            skill.execute_tool("nonexistent", {"device_id": "sala.persiana"})
