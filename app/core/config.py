from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    app_name: str = Field(
        default="Engenharia Fullstack API",
        validation_alias="APP_NAME",
    )
    app_version: str = Field(
        default="0.2.0",
        validation_alias="APP_VERSION",
    )
    debug: bool = Field(
        default=True,
        validation_alias="DEBUG",
    )
    sql_echo: bool = Field(
        default=False,
        validation_alias="SQL_ECHO",
    )

    postgres_user: str = Field(validation_alias="POSTGRES_USER")
    postgres_password: str = Field(validation_alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(validation_alias="POSTGRES_DB")
    postgres_host: str = Field(
        default="localhost",
        validation_alias="POSTGRES_HOST",
    )
    postgres_port: int = Field(
        default=5432,
        validation_alias="POSTGRES_PORT",
    )

    cors_origins_value: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins_value.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()