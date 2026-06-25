from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Modo de operación ---
    mode: str = "simulation"  # "simulation" | "production"

    # --- Servidor ---
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    # --- Ollama (LLM local) ---
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 512

    # --- Arquitectura de Skills ---
    skills_package: str = "src.agent.skills"

    @property
    def is_simulation(self) -> bool:
        return self.mode.lower() == "simulation"

    @property
    def mqtt_topic_prefix(self) -> str:
        return "sim/" if self.is_simulation else "home/"


settings = Settings()
