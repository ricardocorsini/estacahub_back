from fastapi import APIRouter, status

from app.core.security import CurrentUser, DatabaseSession
from app.schemas.sondagens import (
    SondagemCreate,
    SondagemDeleteResponse,
    SondagemResponse,
    SondagemUpdate,
)
from app.services.sondagens_service import (
    atualizar_sondagem_service,
    criar_sondagem_service,
    listar_sondagens_service,
    remover_sondagem_service,
)


router = APIRouter(
    prefix="/obras/{obra_id}/sondagens",
    tags=["sondagens"],
)


@router.get(
    "",
    response_model=list[SondagemResponse],
    response_model_by_alias=True,
)
def listar_sondagens(
    obra_id: int,
    db: DatabaseSession,
    usuario: CurrentUser,
):
    return listar_sondagens_service(db, obra_id, usuario.id)


@router.post(
    "",
    response_model=SondagemResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
def criar_sondagem(
    obra_id: int,
    payload: SondagemCreate,
    db: DatabaseSession,
    usuario: CurrentUser,
):
    return criar_sondagem_service(
        db,
        obra_id,
        usuario.id,
        payload,
    )


@router.put(
    "/{sondagem_id}",
    response_model=SondagemResponse,
    response_model_by_alias=True,
)
def atualizar_sondagem(
    obra_id: int,
    sondagem_id: int,
    payload: SondagemUpdate,
    db: DatabaseSession,
    usuario: CurrentUser,
):
    return atualizar_sondagem_service(
        db,
        obra_id,
        sondagem_id,
        usuario.id,
        payload,
    )


@router.delete(
    "/{sondagem_id}",
    response_model=SondagemDeleteResponse,
)
def remover_sondagem(
    obra_id: int,
    sondagem_id: int,
    db: DatabaseSession,
    usuario: CurrentUser,
):
    return remover_sondagem_service(
        db,
        obra_id,
        sondagem_id,
        usuario.id,
    )
