from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, Field, SecretStr, TypeAdapter
from pydantic_settings import BaseSettings, SettingsConfigDict

URL_ADAPTER = TypeAdapter(AnyUrl)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.local", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["local", "ci", "staging", "production"] = "local"
    app_name: str = "pokerinsight"
    app_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    app_version: str = "0.0.0"
    app_base_url: AnyUrl = Field(
        default_factory=lambda: URL_ADAPTER.validate_python("http://localhost:8000")
    )
    git_sha: str = "local"

    database_url: str
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=10, ge=0, le=100)
    database_echo: bool = False

    redis_url: str
    redis_celery_broker: str = "redis://localhost:6379/3"
    redis_celery_result: str = "redis://localhost:6379/3"
    redis_cache: str = "redis://localhost:6379/0"
    redis_ratelimit: str = "redis://localhost:6379/2"

    s3_endpoint: AnyUrl = Field(
        default_factory=lambda: URL_ADAPTER.validate_python("http://localhost:9000")
    )
    s3_region: str = "auto"
    s3_bucket_hh: str = "pokerinsight-dev"
    s3_bucket_exports: str = "pi-exports"
    s3_access_key_id: str = "minio_dev"
    s3_secret_access_key: SecretStr = SecretStr("minio_dev_secret")

    jwt_private_key_path: str = "/run/secrets/jwt_priv.pem"
    jwt_public_key_path: str = "/run/secrets/jwt_pub.pem"
    jwt_access_ttl_seconds: int = Field(default=900, ge=60)
    jwt_refresh_ttl_seconds: int = Field(default=2_592_000, ge=3600)
    argon2_time_cost: int = Field(default=3, ge=1)
    argon2_memory_cost: int = Field(default=65_536, ge=1024)
    argon2_parallelism: int = Field(default=4, ge=1)

    google_oauth_client_id: str = ""
    google_oauth_client_secret: SecretStr = SecretStr("")

    stripe_secret_key: SecretStr = SecretStr("")
    stripe_webhook_secret: SecretStr = SecretStr("")
    stripe_pro_price_id: str = ""

    resend_api_key: SecretStr = SecretStr("")
    email_from: str = "no-reply@pokerinsight.app"
    email_reply_to: str = "suporte@pokerinsight.app"

    sentry_dsn: str = ""
    otel_exporter_otlp_endpoint: AnyUrl = Field(
        default_factory=lambda: URL_ADAPTER.validate_python("http://localhost:4318")
    )
    otel_service_name: str = "pokerinsight-api"

    free_hands_quota_30d: int = Field(default=5000, ge=0)
    pro_hands_quota_30d: int = Field(default=0, ge=0)
    max_upload_mb_free: int = Field(default=50, ge=1)
    max_upload_mb_pro: int = Field(default=200, ge=1)

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
