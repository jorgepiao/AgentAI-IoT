import pytest
from pydantic import ValidationError

from src.core.guardrails import (
    DEVICE_REGISTRY,
    DeviceCommand,
    LightCommand,
    ClimateCommand,
    CoverCommand,
    FanCommand,
    validate_command,
)


class TestDeviceCommand:
    def test_valid_device(self):
        cmd = DeviceCommand(device_id="sala.luz_principal", action="on")
        assert cmd.device_id == "sala.luz_principal"
        assert cmd.action == "on"

    def test_unknown_device(self):
        with pytest.raises(ValueError, match="Dispositivo desconocido"):
            DeviceCommand(device_id="inexistente", action="on")

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError, match="extra_forbidden"):
            DeviceCommand(device_id="sala.luz_principal", action="on", extra="no")


class TestLightCommand:
    def test_light_on_valid(self):
        cmd = LightCommand(device_id="sala.luz_principal", action="on")
        assert cmd.action == "on"

    def test_light_set_brightness_valid(self):
        cmd = LightCommand(
            device_id="sala.luz_principal",
            action="set_brightness",
            params={"brightness": 75},
        )
        assert cmd.params["brightness"] == 75

    def test_light_set_brightness_out_of_range(self):
        with pytest.raises(ValueError, match="Brightness.*0-100"):
            LightCommand(
                device_id="sala.luz_principal",
                action="set_brightness",
                params={"brightness": 150},
            )

    def test_light_set_brightness_negative(self):
        with pytest.raises(ValueError, match="Brightness.*0-100"):
            LightCommand(
                device_id="sala.luz_principal",
                action="set_brightness",
                params={"brightness": -5},
            )

    def test_climate_device_rejected_by_light_schema(self):
        with pytest.raises(ValueError, match="no es un dispositivo de iluminación"):
            LightCommand(
                device_id="sala.aire_acondicionado",
                action="on",
            )


class TestClimateCommand:
    def test_set_temperature_valid(self):
        cmd = ClimateCommand(
            device_id="sala.aire_acondicionado",
            action="set_temperature",
            params={"temperature": 24},
        )
        assert cmd.params["temperature"] == 24

    def test_set_temperature_too_high(self):
        with pytest.raises(ValueError, match="Temperatura.*16-30"):
            ClimateCommand(
                device_id="sala.aire_acondicionado",
                action="set_temperature",
                params={"temperature": 35},
            )

    def test_set_temperature_too_low(self):
        with pytest.raises(ValueError, match="Temperatura.*16-30"):
            ClimateCommand(
                device_id="sala.aire_acondicionado",
                action="set_temperature",
                params={"temperature": 10},
            )

    def test_turn_off_climate(self):
        cmd = ClimateCommand(
            device_id="sala.aire_acondicionado", action="off"
        )
        assert cmd.action == "off"

    def test_light_device_rejected_by_climate_schema(self):
        with pytest.raises(ValueError, match="no es un dispositivo de clima"):
            ClimateCommand(
                device_id="sala.luz_principal",
                action="off",
            )


class TestCoverCommand:
    def test_cover_open_valid(self):
        cmd = CoverCommand(device_id="sala.persiana", action="open")
        assert cmd.action == "open"

    def test_cover_close_valid(self):
        cmd = CoverCommand(device_id="sala.persiana", action="close")
        assert cmd.action == "close"

    def test_cover_set_position_valid(self):
        cmd = CoverCommand(
            device_id="sala.persiana",
            action="set_position",
            params={"position": 50},
        )
        assert cmd.params["position"] == 50

    def test_cover_set_position_out_of_range(self):
        with pytest.raises(ValueError, match="Posición.*0-100"):
            CoverCommand(
                device_id="sala.persiana",
                action="set_position",
                params={"position": 150},
            )

    def test_cover_set_position_negative(self):
        with pytest.raises(ValueError, match="Posición.*0-100"):
            CoverCommand(
                device_id="sala.persiana",
                action="set_position",
                params={"position": -5},
            )

    def test_non_cover_device_rejected(self):
        with pytest.raises(ValueError, match="no es una persiana"):
            CoverCommand(
                device_id="sala.luz_principal",
                action="open",
            )


class TestFanCommand:
    def test_fan_on_valid(self):
        cmd = FanCommand(device_id="sala.ventilador", action="on")
        assert cmd.action == "on"

    def test_fan_off_valid(self):
        cmd = FanCommand(device_id="sala.ventilador", action="off")
        assert cmd.action == "off"

    def test_fan_set_speed_valid(self):
        cmd = FanCommand(
            device_id="sala.ventilador",
            action="set_speed",
            params={"speed": 75},
        )
        assert cmd.params["speed"] == 75

    def test_fan_set_speed_out_of_range(self):
        with pytest.raises(ValueError, match="Velocidad.*0-100"):
            FanCommand(
                device_id="sala.ventilador",
                action="set_speed",
                params={"speed": 120},
            )

    def test_fan_set_speed_negative(self):
        with pytest.raises(ValueError, match="Velocidad.*0-100"):
            FanCommand(
                device_id="sala.ventilador",
                action="set_speed",
                params={"speed": -1},
            )

    def test_non_fan_device_rejected(self):
        with pytest.raises(ValueError, match="no es un ventilador"):
            FanCommand(
                device_id="sala.luz_principal",
                action="on",
            )


class TestValidateCommand:
    def test_validate_light_command(self):
        result = validate_command({
            "device_id": "oficina.luz_escritorio",
            "action": "set_brightness",
            "params": {"brightness": 50},
        })
        assert isinstance(result, LightCommand)

    def test_validate_climate_command(self):
        result = validate_command({
            "device_id": "dormitorio.calefactor",
            "action": "set_temperature",
            "params": {"temperature": 22},
        })
        assert isinstance(result, ClimateCommand)

    def test_validate_unknown_device_raises(self):
        with pytest.raises(ValueError, match="Dispositivo desconocido"):
            validate_command({
                "device_id": "dispositivo.desconocido",
                "action": "on",
            })

    def test_validate_invalid_params_raises(self):
        with pytest.raises(ValueError, match="Temperatura.*16-30"):
            validate_command({
                "device_id": "dormitorio.calefactor",
                "action": "set_temperature",
                "params": {"temperature": 50},
            })

    def test_validate_cover_command(self):
        result = validate_command({
            "device_id": "sala.persiana",
            "action": "set_position",
            "params": {"position": 50},
        })
        assert isinstance(result, CoverCommand)

    def test_validate_fan_command(self):
        result = validate_command({
            "device_id": "sala.ventilador",
            "action": "set_speed",
            "params": {"speed": 75},
        })
        assert isinstance(result, FanCommand)

    def test_validate_switch_command_falls_to_base(self):
        result = validate_command({
            "device_id": "oficina.enchufe",
            "action": "on",
            "params": {},
        })
        assert isinstance(result, DeviceCommand)

    def test_validate_appliance_command_falls_to_base(self):
        result = validate_command({
            "device_id": "cocina.cafetera",
            "action": "off",
            "params": {},
        })
        assert isinstance(result, DeviceCommand)
