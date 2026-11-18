from typing import Annotated

from fastapi import APIRouter, Path, status

from app.core.security import CurrentUser, DatabaseSession
from app.schemas.carga_admissivel import CargaAdmissivelRequest, CargaAdmissivelResponse
from app.schemas.estacas import EstacaCreate, EstacaDeleteResponse, EstacaResponse, EstacaUpdate
from app.services.carga_admissivel_service import calcular_carga_admissivel_service
from app.services.estacas_service import (
    atualizar_estaca_service, criar_estaca_service, listar_estacas_service,
    obter_estaca_service, remover_estaca_service,
)

router = APIRouter(prefix="/obras/{obra_id}/estacas", tags=["estacas"])


@router.get("", response_model=list[EstacaResponse])
def listar_estacas(obra_id: int, db: DatabaseSession, usuario: CurrentUser):
    return listar_estacas_service(db, obra_id, usuario.id)


@router.post("", response_model=EstacaResponse, status_code=status.HTTP_201_CREATED)
def criar_estaca(obra_id: int, payload: EstacaCreate, db: DatabaseSession, usuario: CurrentUser):
    return criar_estaca_service(db, obra_id, usuario.id, payload)


@router.get("/{estaca_id}", response_model=EstacaResponse)
def obter_estaca(obra_id: int, estaca_id: int, db: DatabaseSession, usuario: CurrentUser):
    return obter_estaca_service(db, obra_id, estaca_id, usuario.id)


@router.post("/{estaca_id}/carga-admissivel", response_model=CargaAdmissivelResponse)
def calcular_carga_admissivel(
    obra_id: Annotated[int, Path(gt=0, le=2**63 - 1)],
    estaca_id: Annotated[int, Path(gt=0, le=2**63 - 1)],
    payload: CargaAdmissivelRequest,
    db: DatabaseSession,
    usuario: CurrentUser,
):
    """Calcula a carga admissível por cota de ponta para uma sondagem da obra."""
    return calcular_carga_admissivel_service(db, obra_id, estaca_id, usuario.id, payload)


@router.put("/{estaca_id}", response_model=EstacaResponse)
def atualizar_estaca(
    obra_id: int, estaca_id: int, payload: EstacaUpdate, db: DatabaseSession, usuario: CurrentUser,
):
    return atualizar_estaca_service(db, obra_id, estaca_id, usuario.id, payload)


@router.delete("/{estaca_id}", response_model=EstacaDeleteResponse)
def remover_estaca(obra_id: int, estaca_id: int, db: DatabaseSession, usuario: CurrentUser):
    return remover_estaca_service(db, obra_id, estaca_id, usuario.id)
