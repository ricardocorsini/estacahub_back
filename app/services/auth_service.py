from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import (
    DUMMY_PASSWORD_HASH,
    gerar_hash_senha,
    verificar_senha,
)
from app.models.usuario import Usuario
from app.schemas.auth import UsuarioCreate


def _buscar_por_email(db: Session, email: str) -> Usuario | None:
    statement = select(Usuario).where(Usuario.email == email.lower())
    return db.scalar(statement)


def criar_usuario_service(
    db: Session,
    payload: UsuarioCreate,
) -> Usuario:
    if _buscar_por_email(db, str(payload.email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta cadastrada com este e-mail.",
        )

    usuario = Usuario(
        nome=payload.nome,
        email=str(payload.email).lower(),
        senha_hash=gerar_hash_senha(payload.senha),
    )

    db.add(usuario)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta cadastrada com este e-mail.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível criar a conta neste momento.",
        ) from exc

    db.refresh(usuario)
    return usuario


def autenticar_usuario_service(
    db: Session,
    email: str,
    senha: str,
) -> Usuario | None:
    usuario = _buscar_por_email(db, email)

    if usuario is None:
        verificar_senha(senha, DUMMY_PASSWORD_HASH)
        return None

    if not verificar_senha(senha, usuario.senha_hash):
        return None

    if not usuario.ativo:
        return None

    usuario.ultimo_login_em = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(usuario)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível concluir o login neste momento.",
        ) from exc

    return usuario
