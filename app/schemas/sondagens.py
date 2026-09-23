from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _valor_vazio_para_none(value):
    if value == "":
        return None
    return value


class DadosCabecalhoSondagem(BaseModel):
    cota_boca: float | None = Field(default=None, alias="cotaBoca")
    profundidade_final: float | None = Field(
        default=None,
        alias="profundidadeFinal",
        ge=0,
    )
    criterio: str | None = Field(default=None, max_length=100)
    nivel_agua: float | None = Field(
        default=None,
        alias="nivelAgua",
        ge=0,
    )
    coord_x: float | None = Field(default=None, alias="coordX")
    coord_y: float | None = Field(default=None, alias="coordY")

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    @field_validator(
        "cota_boca",
        "profundidade_final",
        "nivel_agua",
        "coord_x",
        "coord_y",
        mode="before",
    )
    @classmethod
    def normalizar_numeros_vazios(cls, value):
        return _valor_vazio_para_none(value)

    @field_validator("criterio", mode="before")
    @classmethod
    def normalizar_criterio_vazio(cls, value):
        return _valor_vazio_para_none(value)


class LeituraSondagemBase(BaseModel):
    profundidade: float | None = Field(default=None, ge=0)
    cota: float | None = None
    nspt: int | None = Field(default=None, ge=0)
    solo: str | None = Field(default=None, max_length=100)
    familia: str | None = Field(default=None, max_length=30)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("profundidade", "cota", "nspt", mode="before")
    @classmethod
    def normalizar_numeros_vazios(cls, value):
        return _valor_vazio_para_none(value)

    @field_validator("solo", "familia", mode="before")
    @classmethod
    def normalizar_textos_vazios(cls, value):
        return _valor_vazio_para_none(value)


class LeituraSondagemResponse(LeituraSondagemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class SondagemPayload(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    dados_cabecalho: DadosCabecalhoSondagem = Field(
        default_factory=DadosCabecalhoSondagem,
        alias="dadosCabecalho",
    )
    leituras: list[LeituraSondagemBase] = Field(
        default_factory=list,
        max_length=500,
    )

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class SondagemCreate(SondagemPayload):
    pass


class SondagemUpdate(SondagemPayload):
    pass


class SondagemResponse(SondagemPayload):
    id: int
    leituras: list[LeituraSondagemResponse]
    criado_em: datetime = Field(alias="criadoEm")
    atualizado_em: datetime = Field(alias="atualizadoEm")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class SondagemDeleteResponse(BaseModel):
    message: str
    id: int
