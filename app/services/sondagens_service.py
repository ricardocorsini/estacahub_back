from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.obra import Obra
from app.models.sondagem import LeituraSondagem, Sondagem
from app.schemas.sondagens import SondagemCreate, SondagemUpdate


def _garantir_obra_pertence_ao_usuario(
    db: Session,
    obra_id: int,
    usuario_id: int,
) -> None:
    statement = select(Obra.id).where(
        Obra.id == obra_id,
        Obra.usuario_id == usuario_id,
    )

    if db.scalar(statement) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Obra não encontrada.",
        )


def _statement_sondagem(
    obra_id: int,
    usuario_id: int,
):
    return (
        select(Sondagem)
        .options(selectinload(Sondagem.leituras))
        .where(
            Sondagem.obra_id == obra_id,
            Sondagem.usuario_id == usuario_id,
        )
    )


def _obter_sondagem_ou_404(
    db: Session,
    obra_id: int,
    sondagem_id: int,
    usuario_id: int,
) -> Sondagem:
    statement = _statement_sondagem(obra_id, usuario_id).where(
        Sondagem.id == sondagem_id,
    )
    sondagem = db.scalar(statement)

    if sondagem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sondagem não encontrada.",
        )

    return sondagem


def _nome_ja_utilizado(
    db: Session,
    obra_id: int,
    usuario_id: int,
    nome: str,
    ignorar_id: int | None = None,
) -> bool:
    statement = select(Sondagem.id).where(
        Sondagem.obra_id == obra_id,
        Sondagem.usuario_id == usuario_id,
        Sondagem.nome == nome,
    )

    if ignorar_id is not None:
        statement = statement.where(Sondagem.id != ignorar_id)

    return db.scalar(statement) is not None


def _aplicar_payload(
    sondagem: Sondagem,
    payload: SondagemCreate | SondagemUpdate,
) -> None:
    cabecalho = payload.dados_cabecalho

    sondagem.nome = payload.nome
    sondagem.cota_boca = cabecalho.cota_boca
    sondagem.profundidade_final = cabecalho.profundidade_final
    sondagem.criterio = cabecalho.criterio
    sondagem.nivel_agua = cabecalho.nivel_agua
    sondagem.coord_x = cabecalho.coord_x
    sondagem.coord_y = cabecalho.coord_y
    sondagem.leituras = [
        LeituraSondagem(
            ordem=indice,
            profundidade=leitura.profundidade,
            cota=leitura.cota,
            nspt=leitura.nspt,
            solo=leitura.solo,
            familia=leitura.familia,
        )
        for indice, leitura in enumerate(payload.leituras)
    ]


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma sondagem com este nome nesta obra.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível salvar os dados da sondagem.",
        ) from exc


def listar_sondagens_service(
    db: Session,
    obra_id: int,
    usuario_id: int,
) -> list[Sondagem]:
    _garantir_obra_pertence_ao_usuario(db, obra_id, usuario_id)
    statement = _statement_sondagem(obra_id, usuario_id).order_by(
        Sondagem.criado_em.asc(),
        Sondagem.id.asc(),
    )
    return list(db.scalars(statement).all())


def criar_sondagem_service(
    db: Session,
    obra_id: int,
    usuario_id: int,
    payload: SondagemCreate,
) -> Sondagem:
    _garantir_obra_pertence_ao_usuario(db, obra_id, usuario_id)

    if _nome_ja_utilizado(db, obra_id, usuario_id, payload.nome):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma sondagem com este nome nesta obra.",
        )

    sondagem = Sondagem(
        obra_id=obra_id,
        usuario_id=usuario_id,
        nome=payload.nome,
    )
    _aplicar_payload(sondagem, payload)
    db.add(sondagem)
    _commit(db)

    return _obter_sondagem_ou_404(
        db,
        obra_id,
        sondagem.id,
        usuario_id,
    )


def atualizar_sondagem_service(
    db: Session,
    obra_id: int,
    sondagem_id: int,
    usuario_id: int,
    payload: SondagemUpdate,
) -> Sondagem:
    _garantir_obra_pertence_ao_usuario(db, obra_id, usuario_id)
    sondagem = _obter_sondagem_ou_404(
        db,
        obra_id,
        sondagem_id,
        usuario_id,
    )

    if _nome_ja_utilizado(
        db,
        obra_id,
        usuario_id,
        payload.nome,
        ignorar_id=sondagem_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma sondagem com este nome nesta obra.",
        )

    _aplicar_payload(sondagem, payload)
    sondagem.atualizado_em = datetime.now(timezone.utc)
    _commit(db)

    return _obter_sondagem_ou_404(
        db,
        obra_id,
        sondagem_id,
        usuario_id,
    )


def remover_sondagem_service(
    db: Session,
    obra_id: int,
    sondagem_id: int,
    usuario_id: int,
) -> dict[str, str | int]:
    _garantir_obra_pertence_ao_usuario(db, obra_id, usuario_id)
    sondagem = _obter_sondagem_ou_404(
        db,
        obra_id,
        sondagem_id,
        usuario_id,
    )

    db.delete(sondagem)
    _commit(db)

    return {
        "message": "Sondagem removida com sucesso.",
        "id": sondagem_id,
    }
