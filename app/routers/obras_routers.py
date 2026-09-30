from fastapi import APIRouter, status

from app.core.security import CurrentUser, DatabaseSession
from app.schemas.obras import (
    ObraCreate,
    ObraDeleteResponse,
    ObraResponse,
    ObraUpdate,
)
from app.services.obras_service import (
    atualizar_obra_parcial_service,
    atualizar_obra_service,
    criar_obra_service,
    listar_obras_service,
    obter_obra_service,
    remover_obra_service,
)


router = APIRouter(
    prefix="/obras",
    tags=["obras"],
)


@router.get(
    "",
    response_model=list[ObraResponse],
    response_model_by_alias=True,
)
def listar_obras(
    db: DatabaseSession,
    usuario: CurrentUser,
):
    return listar_obras_service(db, usuario.id)


@router.post(
    "",
    response_model=ObraResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
def criar_obra(
    payload: ObraCreate,
    db: DatabaseSession,
    usuario: CurrentUser,
):
    return criar_obra_service(db, usuario.id, payload)


@router.get(
    "/{obra_id}",
    response_model=ObraResponse,
    response_model_by_alias=True,
)
def obter_obra(
    obra_id: int,
    db: DatabaseSession,
    usuario: CurrentUser,
):
    return obter_obra_service(db, obra_id, usuario.id)


@router.put(
    "/{obra_id}",
    response_model=ObraResponse,
    response_model_by_alias=True,
)
def atualizar_obra(
    obra_id: int,
    payload: ObraCreate,
    db: DatabaseSession,
    usuario: CurrentUser,
):
    return atualizar_obra_service(
        db,
        obra_id,
        usuario.id,
        payload,
    )


@router.patch(
    "/{obra_id}",
    response_model=ObraResponse,
    response_model_by_alias=True,
)
def atualizar_obra_parcial(
    obra_id: int,
    payload: ObraUpdate,
    db: DatabaseSession,
    usuario: CurrentUser,
):
    return atualizar_obra_parcial_service(
        db,
        obra_id,
        usuario.id,
        payload,
    )


@router.delete(
    "/{obra_id}",
    response_model=ObraDeleteResponse,
)
def remover_obra(
    obra_id: int,
    db: DatabaseSession,
    usuario: CurrentUser,
):
    return remover_obra_service(db, obra_id, usuario.id)
