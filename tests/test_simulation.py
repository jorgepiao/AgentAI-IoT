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

    def test_describe_cover_open(self):
        msg = describe_command(
            "sim/sala/actuator/persiana/set",
            {"action": "open", "params": {}},
        )
        assert "Persiana" in msg
        assert "SUBIR" in msg

    def test_describe_cover_close(self):
        msg = describe_command(
            "sim/sala/actuator/persiana/set",
            {"action": "close"},
        )
        assert "BAJAR" in msg

    def test_describe_cover_set_position(self):
        msg = describe_command(
            "sim/sala/actuator/persiana/set",
            {"action": "set_position", "params": {"position": 50}},
        )
        assert "POSICIÓN" in msg
        assert "50%" in msg

    def test_describe_fan_on(self):
        msg = describe_command(
            "sim/sala/actuator/ventilador/set",
            {"action": "on", "params": {}},
        )
        assert "Ventilador" in msg
        assert "ENCENDIDO" in msg

    def test_describe_fan_off(self):
        msg = describe_command(
            "sim/sala/actuator/ventilador/set",
            {"action": "off"},
        )
        assert "APAGADO" in msg

    def test_describe_fan_set_speed(self):
        msg = describe_command(
            "sim/sala/actuator/ventilador/set",
            {"action": "set_speed", "params": {"speed": 50}},
        )
        assert "VELOCIDAD" in msg
        assert "50%" in msg

    def test_describe_appliance_on(self):
        msg = describe_command(
            "sim/cocina/actuator/cafetera/set",
            {"action": "on", "params": {}},
        )
        assert "Cafetera" in msg
        assert "ENCENDIDO" in msg

    def test_describe_appliance_off(self):
        msg = describe_command(
            "sim/cocina/actuator/cafetera/set",
            {"action": "off"},
        )
        assert "APAGADO" in msg

    def test_describe_switch_on(self):
        msg = describe_command(
            "sim/oficina/actuator/enchufe/set",
            {"action": "on", "params": {}},
        )
        assert "Enchufe" in msg
        assert "ENCENDIDO" in msg

    def test_describe_switch_off(self):
        msg = describe_command(
            "sim/oficina/actuator/enchufe/set",
            {"action": "off"},
        )
        assert "APAGADO" in msg


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

    def test_cover_open_status(self):
        status = build_status_response(
            "sim/sala/actuator/persiana/set",
            {"action": "open", "params": {}},
        )
        assert status["state"] == "on"
        assert status["position"] == 100

    def test_cover_close_status(self):
        status = build_status_response(
            "sim/sala/actuator/persiana/set",
            {"action": "close", "params": {}},
        )
        assert status["state"] == "off"
        assert status["position"] == 0

    def test_cover_set_position_status(self):
        status = build_status_response(
            "sim/sala/actuator/persiana/set",
            {"action": "set_position", "params": {"position": 60}},
        )
        assert status["state"] == "on"
        assert status["position"] == 60

    def test_fan_on_status(self):
        status = build_status_response(
            "sim/sala/actuator/ventilador/set",
            {"action": "on", "params": {}},
        )
        assert status["state"] == "on"
        assert status["speed"] == 100

    def test_fan_off_status(self):
        status = build_status_response(
            "sim/sala/actuator/ventilador/set",
            {"action": "off", "params": {}},
        )
        assert status["state"] == "off"

    def test_fan_set_speed_status(self):
        status = build_status_response(
            "sim/sala/actuator/ventilador/set",
            {"action": "set_speed", "params": {"speed": 60}},
        )
        assert status["state"] == "on"
        assert status["speed"] == 60

    def test_switch_on_status(self):
        status = build_status_response(
            "sim/oficina/actuator/enchufe/set",
            {"action": "on", "params": {}},
        )
        assert status["state"] == "on"

    def test_switch_off_status(self):
        status = build_status_response(
            "sim/oficina/actuator/enchufe/set",
            {"action": "off", "params": {}},
        )
        assert status["state"] == "off"

    def test_appliance_on_status(self):
        status = build_status_response(
            "sim/cocina/actuator/cafetera/set",
            {"action": "on", "params": {}},
        )
        assert status["state"] == "on"

    def test_appliance_off_status(self):
        status = build_status_response(
            "sim/cocina/actuator/cafetera/set",
            {"action": "off", "params": {}},
        )
        assert status["state"] == "off"
