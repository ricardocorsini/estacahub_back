from functools import lru_cache

from pydantic import Field, SecretStr
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

    # ==========================================================
    # PostgreSQL
    # ==========================================================

    postgres_user: str = Field(
        validation_alias="POSTGRES_USER",
    )

    postgres_password: str = Field(
        validation_alias="POSTGRES_PASSWORD",
    )

    postgres_db: str = Field(
        validation_alias="POSTGRES_DB",
    )

    # IMPORTANTE:
    # Dentro do Docker Compose, o hostname é o nome do serviço.
    # Portanto:
    #   postgres -> container PostgreSQL
    #
    # Não usar "localhost" quando a API também estiver
    # executando dentro de um container.
    postgres_host: str = Field(
        default="postgres",
        validation_alias="POSTGRES_HOST",
    )

    # Porta INTERNA do PostgreSQL na rede Docker.
    postgres_port: int = Field(
        default=5432,
        validation_alias="POSTGRES_PORT",
    )

    # ==========================================================
    # CORS
    # ==========================================================

    cors_origins_value: str = Field(
        default=(
            "https://www.estacahub.com,https://estacahub.com,"
            "http://localhost:5173,http://127.0.0.1:5173"
        ),
        validation_alias="CORS_ORIGINS",
    )

    # ==========================================================
    # Autenticação
    # ==========================================================

    jwt_secret_key: SecretStr = Field(
        validation_alias="JWT_SECRET_KEY",
    )

    jwt_algorithm: str = Field(
        default="HS256",
        validation_alias="JWT_ALGORITHM",
    )

    access_token_expire_minutes: int = Field(
        default=1440,
        gt=0,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    auth_cookie_name: str = Field(
        default="estacahub_access_token",
        validation_alias="AUTH_COOKIE_NAME",
    )

    auth_cookie_secure: bool | None = Field(
        default=None,
        validation_alias="AUTH_COOKIE_SECURE",
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

    @property
    def cookie_secure(self) -> bool:
        """
        Usa cookie seguro em produção e permite HTTP no desenvolvimento.
        AUTH_COOKIE_SECURE pode sobrescrever o comportamento automático.
        """

        if self.auth_cookie_secure is not None:
            return self.auth_cookie_secure

        return not self.debug


@lru_cache
def get_settings() -> Settings:
    return Settings()
