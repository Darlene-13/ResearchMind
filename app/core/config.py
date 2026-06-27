from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    anthropic_api_key: str = Field(..., description="Anthropic API key")

    # Orchestrator models
    orchestator_model:str = "claude-sonnet-4-6"
    extractor_model: str = "claude-haiku-4-5"
    writer_model: str = "claude-sonnet-4-6"

    # Maximum tokens a writer can produce
    max_report_tokens:int = 4096
