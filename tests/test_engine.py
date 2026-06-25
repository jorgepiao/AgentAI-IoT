import pytest

from src.agent.engine import Engine
from src.agent.skills.base import Skill, ToolDefinition


class SkillMockLuz(Skill):
    name: str = "iluminacion"
    description: str = "Control de luces y dimmers"
    keywords: list[str] = ["luz", "luces", "ilumina", "foco", "brillo"]

    def get_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="set_light",
                description="Encender, apagar o ajustar brillo de una luz",
                parameters={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string"},
                        "action": {"type": "string", "enum": ["on", "off", "set_brightness"]},
                        "params": {
                            "type": "object",
                            "properties": {
                                "brightness": {"type": "integer", "minimum": 0, "maximum": 100}
                            },
                        },
                    },
                    "required": ["device_id", "action"],
                },
            )
        ]

    def execute_tool(self, tool_name: str, params: dict) -> dict:
        return {"status": "ok", "tool": tool_name, "params": params}


class SkillMockClima(Skill):
    name: str = "clima"
    description: str = "Control de clima, AC y calefacción"
    keywords: list[str] = ["frío", "calor", "temperatura", "clima", "ac", "calefacción"]

    def get_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="set_climate",
                description="Ajustar temperatura o modo del clima",
                parameters={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string"},
                        "action": {"type": "string", "enum": ["set_temperature", "set_mode", "off"]},
                        "params": {
                            "type": "object",
                            "properties": {
                                "temperature": {"type": "number", "minimum": 16, "maximum": 30}
                            },
                        },
                    },
                    "required": ["device_id", "action"],
                },
            )
        ]

    def execute_tool(self, tool_name: str, params: dict) -> dict:
        return {"status": "ok", "tool": tool_name, "params": params}


@pytest.fixture
def engine_with_skills():
    eng = Engine()
    eng.register_skill(SkillMockLuz())
    eng.register_skill(SkillMockClima())
    return eng


class TestEngineSkills:
    def test_register_and_list_skills(self, engine_with_skills):
        assert len(engine_with_skills.skills) == 2
        assert "iluminacion" in engine_with_skills.skills
        assert "clima" in engine_with_skills.skills

    def test_detect_skill_light(self, engine_with_skills):
        skill = engine_with_skills.detect_skill("enciende las luces de la sala")
        assert skill is not None
        assert skill.name == "iluminacion"

    def test_detect_skill_climate(self, engine_with_skills):
        skill = engine_with_skills.detect_skill("tengo mucho calor, baja la temperatura")
        assert skill is not None
        assert skill.name == "clima"

    def test_detect_skill_no_match(self, engine_with_skills):
        skill = engine_with_skills.detect_skill("reproduce música en la sala")
        assert skill is None


class TestEnginePrompt:
    def test_build_prompt_contains_skill_name(self, engine_with_skills):
        skill = engine_with_skills.skills["iluminacion"]
        prompt = engine_with_skills.build_prompt("test", skill)
        assert "iluminacion" in prompt
        assert "set_light" in prompt

    def test_build_prompt_contains_user_message(self, engine_with_skills):
        skill = engine_with_skills.skills["clima"]
        prompt = engine_with_skills.build_prompt("pone el aire a 24 grados", skill)
        assert "pone el aire a 24 grados" in prompt


class TestEngineProcess:
    @pytest.mark.asyncio
    async def test_process_with_mock_llm_valid(self, engine_with_skills):
        async def mock_llm(prompt: str) -> str:
            return '{"device_id": "sala.luz_principal", "action": "on", "params": {}}'

        result = await engine_with_skills.process("enciende las luces", llm_callable=mock_llm)
        assert result["validated"] is True
        assert result["skill"] == "iluminacion"
        assert result["device_id"] == "sala.luz_principal"
        assert result["action"] == "on"

    @pytest.mark.asyncio
    async def test_process_with_mock_llm_invalid_json(self, engine_with_skills):
        async def mock_llm(prompt: str) -> str:
            return "esto no es json"

        result = await engine_with_skills.process("enciende las luces", llm_callable=mock_llm)
        assert "error" in result
        assert "JSON" in result["error"]

    @pytest.mark.asyncio
    async def test_process_with_mock_llm_invalid_device(self, engine_with_skills):
        async def mock_llm(prompt: str) -> str:
            return '{"device_id": "inexistente", "action": "on", "params": {}}'

        result = await engine_with_skills.process("enciende las luces", llm_callable=mock_llm)
        assert "error" in result
        assert "Dispositivo desconocido" in result["error"]

    @pytest.mark.asyncio
    async def test_process_no_skill_detected(self, engine_with_skills):
        async def mock_llm(prompt: str) -> str:
            return '{"device_id": "sala.luz_principal", "action": "on"}'

        result = await engine_with_skills.process("reproduce música", llm_callable=mock_llm)
        assert "error" in result
        assert "No se reconoció" in result["error"]

    @pytest.mark.asyncio
    async def test_process_with_mock_llm_out_of_range(self, engine_with_skills):
        async def mock_llm(prompt: str) -> str:
            return '{"device_id": "sala.aire_acondicionado", "action": "set_temperature", "params": {"temperature": 50}}'

        result = await engine_with_skills.process("sube la temperatura a 50", llm_callable=mock_llm)
        assert "error" in result
        assert "Temperatura" in result["error"]

    @pytest.mark.asyncio
    async def test_process_no_llm_callable_raises(self, engine_with_skills):
        with pytest.raises(NotImplementedError, match="LLM no configurado"):
            await engine_with_skills.process("enciende las luces")


class TestToolDefinition:
    def test_tool_definition_creation(self):
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}},
        )
        assert tool.name == "test_tool"
        assert tool.model_dump()["name"] == "test_tool"


class TestIntegrationRealSkills:
    @pytest.fixture
    def engine_with_real_skills(self):
        from src.agent.skills.climate import ClimateSkill
        from src.agent.skills.lighting import LightingSkill

        eng = Engine()
        eng.register_skill(ClimateSkill())
        eng.register_skill(LightingSkill())
        return eng

    @pytest.mark.asyncio
    async def test_lighting_skill_real(self, engine_with_real_skills):
        async def mock_llm(prompt: str) -> str:
            return '{"device_id": "sala.luz_principal", "action": "on", "params": {}}'

        result = await engine_with_real_skills.process(
            "enciende las luces de la sala", llm_callable=mock_llm
        )
        assert result["validated"] is True
        assert result["skill"] == "iluminacion"
        assert result["device_id"] == "sala.luz_principal"

    @pytest.mark.asyncio
    async def test_climate_skill_real(self, engine_with_real_skills):
        async def mock_llm(prompt: str) -> str:
            return (
                '{"device_id": "sala.aire_acondicionado", '
                '"action": "set_temperature", '
                '"params": {"temperature": 24}}'
            )

        result = await engine_with_real_skills.process(
            "pon el aire a 24 grados", llm_callable=mock_llm
        )
        assert result["validated"] is True
        assert result["skill"] == "clima"
        assert result["device_id"] == "sala.aire_acondicionado"
        assert result["params"]["temperature"] == 24

    @pytest.mark.asyncio
    async def test_llm_returns_wrong_device_type_still_validates(self, engine_with_real_skills):
        async def mock_llm(prompt: str) -> str:
            return '{"device_id": "sala.luz_principal", "action": "off", "params": {}}'

        result = await engine_with_real_skills.process(
            "apaga el clima", llm_callable=mock_llm
        )
        assert result["validated"] is True
        assert result["skill"] == "clima"
        assert result["device_id"] == "sala.luz_principal"

    @pytest.mark.asyncio
    async def test_router_selects_correct_skill_by_keyword(self, engine_with_real_skills):
        assert engine_with_real_skills.detect_skill("prende la luz").name == "iluminacion"
        assert engine_with_real_skills.detect_skill("sube la temperatura").name == "clima"
        assert engine_with_real_skills.detect_skill("música") is None
