from operator import truediv

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

    # Tavily search
    tavily_api_key: str = Field(..., description="tavily api key")

    # How many web results to fetch per sub question
    tavily_max_results: int = 5

    # Database configurations. Postgres with pgvector extension
    database_url: str = Field(...,
                              description="Async Postgres database url")

    # Redis configurations
    redis_url: str = Field(
                           description="Redis connection url",
                           default="redis://localhost:6379"
                           )


    redis_channel_prefix:str = "researchmind:job"

    redis_ttl_seconds: int = 3600 # 1 hour
    # Orchestrator Agent Behavior
    confidence_threshold: float = 0.75
    # Hard limit on search loop iterations
    max_iterations: int = 3

    # Lang smith observability
    langchain_api_key: str = Field(
        default = "",
        description="LangSmith API key. Leave empty to disable tracing."
    )
    langchain_tracing_v2: bool = True
    langchain_project: str = "researchmind"

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def langsmith_enabled(self) -> bool:
        return bool(self.langchain_api_key)


# Single instance to be imported everywhere
settings = Settings()

