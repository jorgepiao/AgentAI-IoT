import pytest
from pydantic import ValidationError

from src.core.guardrails import (
    DEVICE_REGISTRY,
    DeviceCommand,
    LightCommand,
    ClimateCommand,
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
