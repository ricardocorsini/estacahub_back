from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.obra import Obra
from app.schemas.obras import ObraCreate, ObraUpdate


FAKE_S3_BUCKET = "engenharia-fullstack-local"
FAKE_S3_REGION = "sa-east-1"


def _obter_obra_ou_404(db: Session, obra_id: int) -> Obra:
    obra = db.get(Obra, obra_id)

    if obra is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Obra não encontrada.",
        )

    return obra


def _gerar_url_s3_ficticia(nome_arquivo: str) -> str:
    extensao = Path(nome_arquivo).suffix.lower()

    if extensao not in {".jpg", ".jpeg", ".png", ".webp"}:
        extensao = ".jpg"

    chave = f"obras/{uuid4()}{extensao}"

    return (
        f"https://{FAKE_S3_BUCKET}.s3."
        f"{FAKE_S3_REGION}.amazonaws.com/{chave}"
    )


def _commit(db: Session) -> None:
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível salvar os dados da obra.",
        ) from exc


def listar_obras_service(db: Session) -> list[Obra]:
    statement = select(Obra).order_by(Obra.id.desc())
    return list(db.scalars(statement).all())


def obter_obra_service(db: Session, obra_id: int) -> Obra:
    return _obter_obra_ou_404(db, obra_id)


def criar_obra_service(
    db: Session,
    payload: ObraCreate,
) -> Obra:
    dados = payload.model_dump()
    nome_arquivo_foto = dados.pop("nome_arquivo_foto", None)

    nova_obra = Obra(
        **dados,
        foto_url=(
            _gerar_url_s3_ficticia(nome_arquivo_foto)
            if nome_arquivo_foto
            else None
        ),
    )

    db.add(nova_obra)
    _commit(db)
    db.refresh(nova_obra)

    return nova_obra


def atualizar_obra_service(
    db: Session,
    obra_id: int,
    payload: ObraCreate,
) -> Obra:
    obra = _obter_obra_ou_404(db, obra_id)

    dados = payload.model_dump()
    nome_arquivo_foto = dados.pop("nome_arquivo_foto", None)

    for campo, valor in dados.items():
        setattr(obra, campo, valor)

    if nome_arquivo_foto:
        obra.foto_url = _gerar_url_s3_ficticia(nome_arquivo_foto)

    _commit(db)
    db.refresh(obra)

    return obra


def atualizar_obra_parcial_service(
    db: Session,
    obra_id: int,
    payload: ObraUpdate,
) -> Obra:
    obra = _obter_obra_ou_404(db, obra_id)

    dados = payload.model_dump(exclude_unset=True)
    nome_arquivo_foto = dados.pop("nome_arquivo_foto", None)

    for campo, valor in dados.items():
        setattr(obra, campo, valor)

    if nome_arquivo_foto:
        obra.foto_url = _gerar_url_s3_ficticia(nome_arquivo_foto)

    _commit(db)
    db.refresh(obra)

    return obra


def remover_obra_service(
    db: Session,
    obra_id: int,
) -> dict[str, str | int]:
    obra = _obter_obra_ou_404(db, obra_id)

    db.delete(obra)
    _commit(db)

    return {
        "message": "Obra removida com sucesso.",
        "id": obra_id,
    }