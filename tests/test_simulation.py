import json
import pytest

from simulation.mock_sensors import build_payload, SENSORS
from simulation.mock_actuadores import describe_command, build_status_response


class TestMockSensors:
    def test_build_payload_has_value_and_unit(self):
        sensor = {"topic": "test", "range": (0, 100), "unit": "percent", "decimals": 0}
        payload = build_payload(sensor)
        assert "value" in payload
        assert "unit" in payload
        assert payload["unit"] == "percent"

    def test_build_payload_value_in_range(self):
        sensor = {"topic": "test", "range": (10, 20), "unit": "celsius", "decimals": 1}
        for _ in range(100):
            payload = build_payload(sensor)
            assert 10 <= payload["value"] <= 20

    def test_build_payload_binary(self):
        sensor = {"topic": "test", "range": (0, 1), "unit": "binary", "decimals": 0}
        payload = build_payload(sensor)
        assert payload["value"] in (0, 1)

    def test_build_payload_decimals(self):
        sensor = {"topic": "test", "range": (0, 1), "unit": "custom", "decimals": 2}
        payload = build_payload(sensor)
        value_str = str(payload["value"])
        if "." in value_str:
            decimals = len(value_str.split(".")[1])
            assert decimals <= 2

    def test_sensors_definition_complete(self):
        for s in SENSORS:
            assert "topic" in s
            assert "range" in s
            assert len(s["range"]) == 2
            assert s["range"][0] <= s["range"][1]

    def test_all_sensors_produce_valid_payload(self):
        for s in SENSORS:
            p = build_payload(s)
            assert isinstance(p["value"], (int, float))
            assert isinstance(p["unit"], str)


class TestMockActuadores:
    def test_describe_light_on(self):
        msg = describe_command("sim/sala/actuator/luz_principal/set", {"action": "on", "params": {}})
        assert "Luz principal" in msg
        assert "ENCENDIDO" in msg

    def test_describe_light_off(self):
        msg = describe_command("sim/sala/actuator/luz_principal/set", {"action": "off"})
        assert "APAGADO" in msg

    def test_describe_brightness(self):
        msg = describe_command(
            "sim/sala/actuator/luz_principal/set",
            {"action": "set_brightness", "params": {"brightness": 75}},
        )
        assert "BRILLO" in msg
        assert "75%" in msg

    def test_describe_set_temperature(self):
        msg = describe_command(
            "sim/sala/actuator/aire_acondicionado/set",
            {"action": "set_temperature", "params": {"temperature": 24}},
        )
        assert "TEMPERATURA" in msg
        assert "24°C" in msg

    def test_describe_set_mode(self):
        msg = describe_command(
            "sim/sala/actuator/aire_acondicionado/set",
            {"action": "set_mode", "params": {"mode": "cool"}},
        )
        assert "MODO" in msg
        assert "COOL" in msg

    def test_describe_unknown_device(self):
        msg = describe_command(
            "sim/garage/actuator/puerta/set",
            {"action": "open"},
        )
        assert "puerta" in msg
        assert "open" in msg


class TestBuildStatusResponse:
    def test_light_on(self):
        status = build_status_response(
            "sim/sala/actuator/luz_principal/set",
            {"action": "on", "params": {}},
        )
        assert status["state"] == "on"
        assert status["brightness"] == 100

    def test_light_off(self):
        status = build_status_response(
            "sim/sala/actuator/luz_principal/set",
            {"action": "off", "params": {}},
        )
        assert status["state"] == "off"

    def test_light_set_brightness(self):
        status = build_status_response(
            "sim/oficina/actuator/luz_escritorio/set",
            {"action": "set_brightness", "params": {"brightness": 50}},
        )
        assert status["brightness"] == 50
        assert status["state"] == "on"

    def test_climate_set_temperature(self):
        status = build_status_response(
            "sim/sala/actuator/aire_acondicionado/set",
            {"action": "set_temperature", "params": {"temperature": 24}},
        )
        assert status["temperature"] == 24
        assert status["mode"] == "cool"
        assert status["state"] == "on"

    def test_climate_off(self):
        status = build_status_response(
            "sim/dormitorio/actuator/calefactor/set",
            {"action": "off", "params": {}},
        )
        assert status["state"] == "off"

    def test_climate_set_mode(self):
        status = build_status_response(
            "sim/sala/actuator/aire_acondicionado/set",
            {"action": "set_mode", "params": {"mode": "heat"}},
        )
        assert status["mode"] == "heat"
        assert status["state"] == "on"

    def test_status_serializable(self):
        status = build_status_response(
            "sim/sala/actuator/luz_principal/set",
            {"action": "on", "params": {}},
        )
        json.dumps(status)
