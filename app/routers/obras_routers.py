from fastapi import APIRouter, status

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


@router.get("", response_model=list[ObraResponse])
def listar_obras() -> list[ObraResponse]:
    return listar_obras_service()


@router.post(
    "",
    response_model=ObraResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_obra(payload: ObraCreate) -> ObraResponse:
    return criar_obra_service(payload)


@router.get("/{obra_id}", response_model=ObraResponse)
def obter_obra(obra_id: int) -> ObraResponse:
    return obter_obra_service(obra_id)


@router.put("/{obra_id}", response_model=ObraResponse)
def atualizar_obra(
    obra_id: int,
    payload: ObraCreate,
) -> ObraResponse:
    return atualizar_obra_service(obra_id, payload)


@router.patch("/{obra_id}", response_model=ObraResponse)
def atualizar_obra_parcial(
    obra_id: int,
    payload: ObraUpdate,
) -> ObraResponse:
    return atualizar_obra_parcial_service(obra_id, payload)


@router.delete("/{obra_id}", response_model=ObraDeleteResponse)
def remover_obra(obra_id: int) -> ObraDeleteResponse:
    return remover_obra_service(obra_id)