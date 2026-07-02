from typing import Literal, Optional

from pydantic import BaseModel, Field

class ObraBase(BaseModel):
    nome: str = Field(..., min_length=1)
    numero: Optional[str] = None
    localizacao: Optional[str] = None
    dataCadastro: Optional[str] = None
    sistemaCoordenadas: Literal["local", "utm"] = "local"
    responsavelTecnico: Optional[str] = None
    observacoes: Optional[str] = None
    legendaFoto: Optional[str] = None


class ObraCreate(ObraBase):
    pass


class ObraUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1)
    numero: Optional[str] = None
    localizacao: Optional[str] = None
    dataCadastro: Optional[str] = None
    sistemaCoordenadas: Optional[Literal["local", "utm"]] = None
    responsavelTecnico: Optional[str] = None
    observacoes: Optional[str] = None
    legendaFoto: Optional[str] = None


class ObraResponse(ObraBase):
    id: int
    criadoEm: str
    atualizadoEm: str


class ObraDeleteResponse(BaseModel):
    message: str
    id: int