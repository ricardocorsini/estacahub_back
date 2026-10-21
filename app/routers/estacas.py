from fastapi import APIRouter, status

from app.core.security import CurrentUser, DatabaseSession
from app.schemas.estacas import EstacaCreate, EstacaDeleteResponse, EstacaResponse, EstacaUpdate
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


@router.put("/{estaca_id}", response_model=EstacaResponse)
def atualizar_estaca(
    obra_id: int, estaca_id: int, payload: EstacaUpdate, db: DatabaseSession, usuario: CurrentUser,
):
    return atualizar_estaca_service(db, obra_id, estaca_id, usuario.id, payload)


@router.delete("/{estaca_id}", response_model=EstacaDeleteResponse)
def remover_estaca(obra_id: int, estaca_id: int, db: DatabaseSession, usuario: CurrentUser):
    return remover_estaca_service(db, obra_id, estaca_id, usuario.id)
