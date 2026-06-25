from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


DEVICE_REGISTRY: dict[str, dict[str, Any]] = {
    "sala.luz_principal": {
        "type": "light",
        "label": "Luz principal de la sala",
        "min_brightness": 0,
        "max_brightness": 100,
    },
    "sala.aire_acondicionado": {
        "type": "climate",
        "label": "Aire acondicionado de la sala",
        "min_temp": 16,
        "max_temp": 30,
    },
    "oficina.luz_escritorio": {
        "type": "light",
        "label": "Luz del escritorio",
        "min_brightness": 0,
        "max_brightness": 100,
    },
    "dormitorio.calefactor": {
        "type": "climate",
        "label": "Calefactor del dormitorio",
        "min_temp": 16,
        "max_temp": 30,
    },
    "sala.persiana": {
        "type": "cover",
        "label": "Persiana motorizada de la sala",
        "min_position": 0,
        "max_position": 100,
    },
    "sala.ventilador": {
        "type": "fan",
        "label": "Ventilador de techo de la sala",
        "min_speed": 0,
        "max_speed": 100,
    },
    "cocina.cafetera": {
        "type": "appliance",
        "label": "Cafetera inteligente",
    },
    "oficina.enchufe": {
        "type": "switch",
        "label": "Enchufe inteligente de la oficina",
    },
}


class DeviceCommand(BaseModel, extra="forbid"):
    device_id: str = Field(..., description="Identificador único del dispositivo")
    action: str = Field(..., description="Acción a ejecutar")
    params: dict[str, Any] = Field(default_factory=dict, description="Parámetros de la acción")

    @model_validator(mode="after")
    def _validate_device_exists(self):
        if self.device_id not in DEVICE_REGISTRY:
            raise ValueError(
                f"Dispositivo desconocido: '{self.device_id}'. "
                f"Dispositivos válidos: {list(DEVICE_REGISTRY.keys())}"
            )
        return self


class LightCommand(DeviceCommand):
    action: Literal["on", "off", "set_brightness"]
    params: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_light_params(self):
        device = DEVICE_REGISTRY.get(self.device_id)
        if not device or device["type"] != "light":
            raise ValueError(f"'{self.device_id}' no es un dispositivo de iluminación")

        if self.action == "set_brightness":
            brightness = self.params.get("brightness", 0)
            lo = device["min_brightness"]
            hi = device["max_brightness"]
            if not isinstance(brightness, (int, float)) or not (lo <= brightness <= hi):
                raise ValueError(
                    f"Brightness debe ser un número entre {lo}-{hi}, recibido: {brightness}"
                )
        return self


class ClimateCommand(DeviceCommand):
    action: Literal["set_temperature", "set_mode", "off"]
    params: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_climate_params(self):
        device = DEVICE_REGISTRY.get(self.device_id)
        if not device or device["type"] != "climate":
            raise ValueError(f"'{self.device_id}' no es un dispositivo de clima")

        if self.action == "set_temperature":
            temp = self.params.get("temperature", 0)
            lo = device["min_temp"]
            hi = device["max_temp"]
            if not isinstance(temp, (int, float)) or not (lo <= temp <= hi):
                raise ValueError(
                    f"Temperatura debe ser un número entre {lo}-{hi}°C, recibido: {temp}"
                )
        return self


class CoverCommand(DeviceCommand):
    action: Literal["open", "close", "set_position"]
    params: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_cover_params(self):
        device = DEVICE_REGISTRY.get(self.device_id)
        if not device or device["type"] != "cover":
            raise ValueError(f"'{self.device_id}' no es una persiana/cubierta")

        if self.action == "set_position":
            position = self.params.get("position", 0)
            lo = device["min_position"]
            hi = device["max_position"]
            if not isinstance(position, (int, float)) or not (lo <= position <= hi):
                raise ValueError(
                    f"Posición debe ser un número entre {lo}-{hi}, recibido: {position}"
                )
        return self


class FanCommand(DeviceCommand):
    action: Literal["on", "off", "set_speed"]
    params: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_fan_params(self):
        device = DEVICE_REGISTRY.get(self.device_id)
        if not device or device["type"] != "fan":
            raise ValueError(f"'{self.device_id}' no es un ventilador")

        if self.action == "set_speed":
            speed = self.params.get("speed", 0)
            lo = device["min_speed"]
            hi = device["max_speed"]
            if not isinstance(speed, (int, float)) or not (lo <= speed <= hi):
                raise ValueError(
                    f"Velocidad debe ser un número entre {lo}-{hi}, recibido: {speed}"
                )
        return self


def validate_command(data: dict[str, Any]) -> DeviceCommand:
    device_id = data.get("device_id", "")
    device = DEVICE_REGISTRY.get(device_id)

    if not device:
        return DeviceCommand(**data)

    type_map = {"light": LightCommand, "climate": ClimateCommand, "cover": CoverCommand, "fan": FanCommand}
    model_class = type_map.get(device["type"], DeviceCommand)

    return model_class(**data)
