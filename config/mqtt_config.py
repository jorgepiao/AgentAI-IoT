from pydantic_settings import BaseSettings, SettingsConfigDict


class MQTTConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="MQTT_",
    )

    host: str = "localhost"
    port: int = 1883
    keepalive: int = 60

    username: str | None = None
    password: str | None = None

    # Tópicos base (no requieren configuración manual)
    # Se construyen dinámicamente: {prefix}/oficina/sensor/temperatura

    @property
    def client_id(self) -> str:
        return f"agentai_{id(self)}"


mqtt_config = MQTTConfig()
