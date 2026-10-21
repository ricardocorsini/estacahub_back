from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.estaca import Estaca
from app.models.obra import Obra
from app.schemas.estacas import EstacaCreate, EstacaUpdate


def _garantir_acesso(db: Session, obra_id: int, usuario_id: int) -> None:
    if db.scalar(select(Obra.id).where(Obra.id == obra_id, Obra.usuario_id == usuario_id)) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Obra não encontrada.")


def _consulta(obra_id: int, usuario_id: int):
    return select(Estaca).where(Estaca.obra_id == obra_id, Estaca.usuario_id == usuario_id)


def _obter(db: Session, obra_id: int, estaca_id: int, usuario_id: int) -> Estaca:
    estaca = db.scalar(_consulta(obra_id, usuario_id).where(Estaca.id == estaca_id))
    if estaca is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Estaca não encontrada.")
    return estaca


def _verificar_nome(db: Session, obra_id: int, nome: str, ignorar_id: int | None = None) -> None:
    consulta = select(Estaca.id).where(
        Estaca.obra_id == obra_id, func.lower(func.btrim(Estaca.nome)) == func.lower(nome),
    )
    if ignorar_id is not None:
        consulta = consulta.where(Estaca.id != ignorar_id)
    if db.scalar(consulta) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma estaca com este nome nesta obra.")


def _salvar(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if getattr(getattr(exc.orig, "diag", None), "constraint_name", None) == "uq_estacas_obra_nome":
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Já existe uma estaca com este nome nesta obra.",
            ) from exc
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Não foi possível salvar. Atualize a obra e verifique os dados.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Não foi possível salvar os dados da estaca.",
        ) from exc


def listar_estacas_service(db: Session, obra_id: int, usuario_id: int) -> list[Estaca]:
    _garantir_acesso(db, obra_id, usuario_id)
    return list(db.scalars(_consulta(obra_id, usuario_id).order_by(Estaca.criado_em, Estaca.id)).all())


def obter_estaca_service(db: Session, obra_id: int, estaca_id: int, usuario_id: int) -> Estaca:
    _garantir_acesso(db, obra_id, usuario_id)
    return _obter(db, obra_id, estaca_id, usuario_id)


def criar_estaca_service(db: Session, obra_id: int, usuario_id: int, payload: EstacaCreate) -> Estaca:
    _garantir_acesso(db, obra_id, usuario_id)
    _verificar_nome(db, obra_id, payload.nome)
    estaca = Estaca(obra_id=obra_id, usuario_id=usuario_id, **payload.model_dump())
    db.add(estaca)
    _salvar(db)
    db.refresh(estaca)
    return estaca


def atualizar_estaca_service(
    db: Session, obra_id: int, estaca_id: int, usuario_id: int, payload: EstacaUpdate,
) -> Estaca:
    _garantir_acesso(db, obra_id, usuario_id)
    estaca = _obter(db, obra_id, estaca_id, usuario_id)
    _verificar_nome(db, obra_id, payload.nome, ignorar_id=estaca_id)
    for campo, valor in payload.model_dump().items():
        setattr(estaca, campo, valor)
    estaca.atualizado_em = datetime.now(timezone.utc)
    _salvar(db)
    db.refresh(estaca)
    return estaca


def remover_estaca_service(db: Session, obra_id: int, estaca_id: int, usuario_id: int) -> dict:
    _garantir_acesso(db, obra_id, usuario_id)
    estaca = _obter(db, obra_id, estaca_id, usuario_id)
    db.delete(estaca)
    _salvar(db)
    return {"message": "Estaca removida com sucesso.", "id": estaca_id}
