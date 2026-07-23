from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ObraBase(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    numero: str | None = Field(default=None, max_length=50)
    localizacao: str | None = Field(default=None, max_length=255)
    data_cadastro: date | None = Field(
        default=None,
        alias="dataCadastro",
    )
    sistema_coordenadas: Literal["local", "utm"] = Field(
        default="local",
        alias="sistemaCoordenadas",
    )
    responsavel_tecnico: str | None = Field(
        default=None,
        alias="responsavelTecnico",
        max_length=255,
    )
    observacoes: str | None = None
    legenda_foto: str | None = Field(
        default=None,
        alias="legendaFoto",
        max_length=255,
    )

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class ObraCreate(ObraBase):
    # Metadado temporário. O arquivo ainda não é enviado.
    nome_arquivo_foto: str | None = Field(
        default=None,
        alias="nomeArquivoFoto",
        max_length=255,
    )


class ObraUpdate(BaseModel):
    nome: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    numero: str | None = Field(default=None, max_length=50)
    localizacao: str | None = Field(default=None, max_length=255)
    data_cadastro: date | None = Field(
        default=None,
        alias="dataCadastro",
    )
    sistema_coordenadas: Literal["local", "utm"] | None = Field(
        default=None,
        alias="sistemaCoordenadas",
    )
    responsavel_tecnico: str | None = Field(
        default=None,
        alias="responsavelTecnico",
        max_length=255,
    )
    observacoes: str | None = None
    legenda_foto: str | None = Field(
        default=None,
        alias="legendaFoto",
        max_length=255,
    )
    nome_arquivo_foto: str | None = Field(
        default=None,
        alias="nomeArquivoFoto",
        max_length=255,
    )

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class ObraResponse(ObraBase):
    id: int
    foto_url: str | None = Field(
        default=None,
        alias="fotoUrl",
    )
    criado_em: datetime = Field(alias="criadoEm")
    atualizado_em: datetime = Field(alias="atualizadoEm")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class ObraDeleteResponse(BaseModel):
    message: str
    id: int