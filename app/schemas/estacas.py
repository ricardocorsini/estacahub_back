from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


TipoEstaca = Literal[
    "helice_continua", "escavada_seco", "escavada_fluido", "pre_moldada_cravada", "raiz",
]


class EstacaPayload(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    coord_x: float = Field(alias="coordX", ge=-999999999, le=999999999)
    coord_y: float = Field(alias="coordY", ge=-999999999, le=999999999)
    tipo: TipoEstaca
    diametro_cm: float = Field(alias="diametroCm", ge=0.000001, le=10000)
    capacidade_estrutural_tf: float = Field(alias="capacidadeEstruturalTf", ge=0.000001, le=999999999)
    cota_arrasamento: float = Field(alias="cotaArrasamento", ge=-999999999, le=999999999)
    carga_prevista_tf: float = Field(alias="cargaPrevistaTf", ge=0, le=999999999)

    model_config = ConfigDict(
        populate_by_name=True, str_strip_whitespace=True, allow_inf_nan=False, extra="forbid",
    )

    @field_validator(
        "coord_x", "coord_y", "diametro_cm", "capacidade_estrutural_tf",
        "cota_arrasamento", "carga_prevista_tf",
    )
    @classmethod
    def limitar_precisao(cls, valor: float) -> float:
        # Evita que o banco arredonde, por exemplo, 314.9999999 para 315,
        # alterando a referência inteira da grade SPT após recarregar.
        if Decimal(str(valor)).normalize().as_tuple().exponent < -6:
            raise ValueError("Use até seis casas decimais.")
        return valor


class EstacaCreate(EstacaPayload):
    pass


class EstacaUpdate(EstacaPayload):
    """PUT recebe o cadastro completo; referências e alertas não são persistidos."""


class EstacaResponse(EstacaPayload):
    id: int
    obra_id: int = Field(alias="obraId")
    criado_em: datetime = Field(alias="criadoEm")
    atualizado_em: datetime = Field(alias="atualizadoEm")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class EstacaDeleteResponse(BaseModel):
    message: str
    id: int
