from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1, max_length=128)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    crea: str | None = None
    empresa: str | None = None
    ativo: bool
    ultimo_login_em: datetime | None = Field(
        default=None,
        alias="ultimoLoginEm",
    )
    criado_em: datetime = Field(alias="criadoEm")
    atualizado_em: datetime = Field(alias="atualizadoEm")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class AuthResponse(BaseModel):
    access_token: str = Field(alias="accessToken")
    token_type: str = Field(default="bearer", alias="tokenType")
    usuario: UsuarioResponse

    model_config = ConfigDict(populate_by_name=True)


class LogoutResponse(BaseModel):
    message: str
