from functools import lru_cache
from typing import Optional, Tuple, Type

from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from chronos.schemas.enums.providers import LLMProvider, StorageProvider


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    secret_key: str = "secret_key"
    debug: bool = False

    # Storage Settings
    storage_provider: StorageProvider = StorageProvider.LOCAL
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_bucket: Optional[str] = None
    s3_region_name: Optional[str] = None
    s3_endpoint_url: Optional[str] = None

    local_storage_dir: str = "storage"
    local_trace_dir: str = "traces"
    cookies_filename: str = "cookie.json"
    trace_path: Optional[str] = f"{local_storage_dir}/{local_trace_dir}"
    cookies_file: Optional[str] = f"{local_storage_dir}/{cookies_filename}"

    # Redis settings
    redis_url: str = "redis://redis:6379/0"

    # NATS Settings
    nats_url: str = "nats://nats:4222"

    # Courier Settings
    courier_host: Optional[str] = None
    courier_api_key: Optional[str] = None

    # Captcha settings
    captcha_host: Optional[str] = None
    captcha_api_key: Optional[str] = None

    # LLM settings
    llm_provider: LLMProvider = LLMProvider.OPENAI

    # OpenAI settings
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4.1"
    openai_temperature: float = 0.8
    openai_max_retries: int = 2

    # Anthropic settings
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-7-sonnet-20250219"
    anthropic_temperature: float = 0.8
    anthropic_max_retries: int = 2

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        source = [
            init_settings,
            EnvSettingsSource(
                settings_cls=settings_cls,
            ),
            DotEnvSettingsSource(
                settings_cls=settings_cls,
                env_file=".env",
            ),
            file_secret_settings,
        ]

        return (*source,)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
